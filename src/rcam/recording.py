from dataclasses import dataclass
from enum import StrEnum
from rcam.video_recording_fileset import VideoRecordingFileset


class RecordingStatus(StrEnum):
    STOPPED = "stopped"
    RECORDING = "recording"


@dataclass
class Recording:
    recording_id: str
    fileset: VideoRecordingFileset
    status: RecordingStatus

    def __init__(
        self, recording_id: str, status: RecordingStatus = RecordingStatus.STOPPED
    ):
        self.recording_id = recording_id
        self.fileset = VideoRecordingFileset(recording_id)
        self.status = status
