from abc import ABC, abstractmethod
from os import PathLike
from datetime import datetime
from rcam.video_recording_fileset import VideoRecordingFileset
from pydantic.dataclasses import dataclass
from rcam.events import Event


@dataclass
class RecordingMetadata:
    start_time: datetime
    end_time: datetime


class RecorderSettings(ABC):
    pass


class VideoRecorderInterface(ABC):
    @abstractmethod
    def start_recording(
        self,
        recording_id: str | PathLike,
        frame_rate: float | None = None,
        triggered_mode: bool = False,
        settings: RecorderSettings | None = None,
    ) -> VideoRecordingFileset:
        pass

    @abstractmethod
    def get_current_recording(self) -> VideoRecordingFileset | None:
        pass

    @abstractmethod
    def enable_triggered_recording_mode(self, enable: bool = True):
        pass

    @abstractmethod
    def stop_recording(self):
        pass

    @abstractmethod
    def get_current_recording_frame_index(self) -> int:
        pass

    @abstractmethod
    def get_number_of_written_frames(self) -> int:
        pass

    @abstractmethod
    def get_frames_per_second(self) -> float:
        pass

    # online viewing
    @abstractmethod
    def start_streaming(self):
        pass

    @abstractmethod
    def stop_streaming(self):
        pass

    @abstractmethod
    def toggle_streaming(self):
        pass

    @abstractmethod
    def is_streaming(self) -> bool:
        pass

    @abstractmethod
    def is_recording(self) -> bool:
        pass

    @abstractmethod
    def add_event(self, event: Event) -> None:
        pass

    @abstractmethod
    def add_metadata(self, metadata: dict) -> None:
        pass


# Mock class for video recorder
class MockVideoRecorder(VideoRecorderInterface):
    def __init__(self):
        self.recording = False
        self.streaming = False
        self.recording_fileset = None
        self.current_frame_index = 0

    def start_recording(
        self,
        recording_id: str | PathLike,
        frame_rate: float | None = None,
        triggered_mode: bool = False,
        settings: RecorderSettings | None = None,
    ) -> VideoRecordingFileset:
        self.recording = True
        self.recording_fileset = VideoRecordingFileset(recording_id=recording_id)
        return self.recording_fileset

    def get_current_recording(self) -> VideoRecordingFileset | None:
        if self.recording:
            return self.recording_fileset
        return None

    def enable_triggered_recording_mode(self, enable: bool = True):
        pass

    def stop_recording(self):
        self.recording = False
        self.recording_fileset = None
        self.current_frame_index = 0

    def get_current_recording_frame_index(self) -> int:
        return self.current_frame_index

    def get_number_of_written_frames(self) -> int:
        return self.current_frame_index

    def get_frames_per_second(self) -> float:
        return 30.0

    def start_streaming(self):
        self.streaming = True
        print("Streaming started")

    def stop_streaming(self):
        self.streaming = False
        print("Streaming stopped")

    def toggle_streaming(self):
        if self.streaming:
            self.stop_streaming()
        else:
            self.start_streaming()

    def is_streaming(self) -> bool:
        return self.streaming

    def is_recording(self) -> bool:
        return self.recording

    def add_event(self, event: Event) -> None:
        print(f"Event added: {event}")

    def add_metadata(self, metadata: dict) -> None:
        print(f"Metadata added: {metadata}")

    def __str__(self) -> str:
        return (
            f"MockVideoRecorder(recording={self.recording}, streaming={self.streaming})"
        )

    def __repr__(self) -> str:
        return (
            f"MockVideoRecorder(recording={self.recording}, streaming={self.streaming})"
        )
