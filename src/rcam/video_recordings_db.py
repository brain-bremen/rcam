from dataclasses import dataclass
from rcam.video_recording_fileset import (
    VideoRecordingFileset,
    recording_id_from_video_filename,
)
import rcam.config as config
import os
from enum import Enum


class RecordingStatus(Enum):
    STOPPED = "stopped"
    RECORDING = "recording"


@dataclass
class Recording:
    fileset: VideoRecordingFileset
    status: RecordingStatus


def update_recordings_from_disk(
    video_extension=config.VIDEO_FILE_EXTENSION,
    recordings_directory=config.RECORDINGS_DIR,
) -> dict[str, Recording]:
    recordings: dict[str, Recording] = {}
    for filename in os.listdir(recordings_directory):
        if filename.endswith(f".{video_extension}"):
            recording_id = recording_id_from_video_filename(filename)
            recordings[recording_id] = Recording(
                fileset=VideoRecordingFileset(recording_id=recording_id),
                status=RecordingStatus.STOPPED,
            )
    return recordings


class SimpleDiskbasedVideoRecordingsDatabase:
    recordings: dict[str, Recording]

    def __contains__(self, recording_id: str) -> bool:
        return recording_id in self.recordings

    def __init__(self):
        self.recordings = update_recordings_from_disk()

    def add_recording(self, recording: Recording):
        self.recordings[recording.fileset.recording_id] = recording

    def get_current_recording(self) -> Recording | None:
        """Get the current recording"""
        for recording in self.recordings.values():
            if recording.status == RecordingStatus.RECORDING:
                return recording
        return None

    def get_recording(self, recording_id: str) -> Recording | None:
        return self.recordings.get(recording_id)

    def update(self):
        self.recordings = update_recordings_from_disk()

    def is_recording_in_progress(self) -> bool:
        return self.get_current_recording() is not None
