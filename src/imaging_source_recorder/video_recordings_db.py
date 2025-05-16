from dataclasses import dataclass
from video_recording_fileset import (
    VideoRecordingFileset,
    recording_id_from_video_filename,
)
import config
import os
from enum import Enum


class RecordingStatus(Enum):
    STOPPED = "stopped"
    RECORDING = "recording"


@dataclass
class Recording:
    fileset: VideoRecordingFileset
    # metadata: Dict[str, str]
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


def get_current_recording() -> Recording | None:
    """Get the current recording"""
    if not recordings:
        return None
    for recording in recordings.values():
        if recording.status == RecordingStatus.RECORDING:
            return recording
    return None


def is_recording_in_progress() -> bool:
    return get_current_recording is not None


recordings: dict[str, Recording] = update_recordings_from_disk()
