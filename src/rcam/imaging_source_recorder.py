import time
from typing import Callable
from rcam.events import EventRecorderInterface, JsonLinesEventRecorder
import imagingcontrol4 as ic4
from rcam.video_recordings_db import Recording, RecordingStatus, VideoRecordingsDatabase
from rcam.video_recorder_interface import (
    VideoRecorderInterface,
)
import logging

logger = logging.getLogger(__name__)  # Uses the global logging configuration


class ImagingSourceRecorder(VideoRecorderInterface):
    sink: ic4.Sink
    grabber: ic4.Grabber
    video_writer: ic4.VideoWriter
    video_capture_pause: bool
    capture_to_video: bool
    stream_start_time: int  # ns
    current_recording_frame_index: int
    event_recorder: EventRecorderInterface
    current_recording: Recording | None
    db: VideoRecordingsDatabase | None
    _event_handlers: list[Callable] = []

    def __init__(
        self,
        db: VideoRecordingsDatabase,
        event_recorder: EventRecorderInterface = JsonLinesEventRecorder(),
    ):
        self.capture_to_video = False
        self.video_capture_pause = False
        self.video_writer = ic4.VideoWriter(ic4.VideoWriterType.MP4_H264)
        self.stream_start_time = 0
        self.current_recording_frame_index = 0
        self.event_recorder = event_recorder
        self.current_recording = None
        self._event_handlers = []
        self.db = db

        class _Listener(ic4.QueueSinkListener):
            def sink_connected(
                self,
                sink: ic4.QueueSink,
                image_type: ic4.ImageType,
                min_buffers_required: int,
            ) -> bool:
                # Allocate more buffers than suggested, because we temporarily take some buffers
                # out of circulation when saving an image or video files.
                sink.alloc_and_queue_buffers(min_buffers_required + 2)
                return True

            def sink_disconnected(self, sink: ic4.QueueSink):
                pass

            def frames_queued(listener, sink: ic4.QueueSink):
                buf = sink.pop_output_buffer()

                # Connect the buffer's chunk data to the device's property map
                # This allows for properties backed by chunk data to be updated
                self.grabber.device_property_map.connect_chunkdata(buf)

                if self.capture_to_video and not self.video_capture_pause:
                    try:
                        self.video_writer.add_frame(buf)
                        self.current_recording_frame_index += 1
                    except ic4.IC4Exception as ex:
                        pass

        self.grabber = ic4.Grabber()

        self.sink = ic4.QueueSink(_Listener())

    # interface methods
    def get_frame_rate_hz(self) -> float:
        return self.grabber.device_property_map.get_value_float(
            ic4.PropId.ACQUISITION_FRAME_RATE
        )

    def get_current_recording(self) -> Recording | None:
        return self.current_recording

    def get_current_recording_frame_index(self):
        return self.current_recording_frame_index

    def start_streaming(self, display: ic4.Display | None = None):
        if not self.grabber.is_device_valid:
            return

        if not self.grabber.is_streaming:
            self.grabber.stream_setup(self.sink, display)
            self.stream_start_time = time.perf_counter_ns()

    def enable_triggered_recording_mode(self, enable: bool = True):
        self.grabber.device_property_map.try_set_value(
            ic4.PropId.TRIGGER_MODE,
            enable,
        )

    def get_triggered_record_mode(self) -> bool:
        return self.grabber.device_property_map.get_value_bool(ic4.PropId.TRIGGER_MODE)

    def is_streaming(self) -> bool:
        return self.grabber.is_streaming

    def is_recording(self) -> bool:
        return self.capture_to_video

    def load_state_from_file(self, filename: str):
        self.grabber.device_open_from_state_file(filename)

    def start_recording(
        self,
        recording_id: str,
        frame_rate=None,
        triggered_mode=False,
        settings=None,
    ):
        if not self.grabber.is_device_valid:
            self.capture_to_video = False
            return

        self.current_recording = Recording(
            recording_id=recording_id, status=RecordingStatus.RECORDING
        )
        if self.db is not None:
            self.db.set_current_recording(self.current_recording)

        self.event_recorder.begin_file(
            self.current_recording.fileset.full_event_filename
        )

        self.current_recording_frame_index = 0
        try:
            self.enable_triggered_recording_mode(triggered_mode)

            if not self.is_streaming():
                self.start_streaming()

            if frame_rate is None:
                frame_rate = self.grabber.device_property_map.get_value_float(
                    ic4.PropId.ACQUISITION_FRAME_RATE
                )

            self.video_writer.begin_file(
                path=self.current_recording.fileset.full_video_filename,
                image_type=self.sink.output_image_type,
                frame_rate=frame_rate,
            )

            self.capture_to_video = True
            logger.info(
                f"Started recording to {self.current_recording.fileset.full_video_filename}"
            )

        except ic4.IC4Exception as ex:
            self.capture_to_video = False
            self.current_recording = None
            raise ex

    def stop_recording(self):
        if self.current_recording is not None:
            self.current_recording.status = RecordingStatus.STOPPED

        if self.db:
            self.db.get_recording(self.current_recording.recording_id)

        self.capture_to_video = False
        self.video_writer.finish_file()
        self.event_recorder.close_file()
        self.current_recording = None
        self.current_fileset = None
        logger.info(
            f"Stopped recording, written {self.current_recording_frame_index} frames"
        )

    def add_event(self, event):
        event.frame = self.current_recording_frame_index
        self.event_recorder.add_event(event)
        for handler in self._event_handlers:
            handler(event)
        logger.debug(f"Added event: {event}")

    def stop_streaming(self):
        if not self.grabber.is_device_valid:
            return

        if self.grabber.is_streaming:
            self.grabber.stream_stop()

        logger.info("Stopped streaming")

    def toggle_streaming(self, display: ic4.Display | None = None):
        if self.grabber.is_device_valid:
            if self.grabber.is_streaming:
                self.grabber.stream_stop()
            else:
                self.start_streaming(display)

    def pause_recording(self):
        self.video_capture_pause = True

    def get_number_of_written_frames(self) -> int:
        return self.current_recording_frame_index

    def get_frames_per_second(self):
        return (
            self.grabber.stream_statistics.sink_delivered
            / (time.perf_counter_ns() - self.stream_start_time)
            * 1e9
        )

    def add_metadata(self, metadata):
        raise NotImplementedError()

    def register_event_handler(self, func):
        self._event_handlers.append(func)

    def __del__(self):
        self.grabber.device_close()
