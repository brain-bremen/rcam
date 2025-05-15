from video_recorder_interface import recording_id_from_video_filename
from video_recording_fileset import VideoRecordingFileset
import os
from enum import Enum

RECORDINGS_DIR = os.path.join(
    os.path.expanduser("~"), "Videos", "ImagingSourceRecorder"
)

# Ensure the recordings directory exists
if not os.path.exists(RECORDINGS_DIR):
    os.makedirs(RECORDINGS_DIR)


class RecordingStatus(Enum):
    STOPPED = "stopped"
    RECORDING = "recording"


@dataclass
class Recording:
    fileset: VideoRecordingFileset
    # metadata: Dict[str, str]
    status: RecordingStatus
    # video_url: str
    # metadata_url: str | None = None
    # event_url: str | None = None


def update_recordings_from_disk(
    video_extension="mp4",
) -> dict[str, VideoRecordingFileset]:
    recordings: dict[str, VideoRecordingFileset] = {}
    for filename in os.listdir(RECORDINGS_DIR):
        if filename.endswith(f".{video_extension}"):
            recording_id = recording_id_from_video_filename(filename)
            dataset = VideoRecordingFileset(
                recording_id=recording_id, video_extension=video_extension
            )

            recordings[recording_id] = VideoRecordingFileset(
                recording_data=dataset,
                status=RecordingStatus.STOPPED,
            )
    return recordings


def get_current_recording() -> VideoRecordingFileset | None:
    """Get the current recording"""
    if not recordings:
        return None
    for recording in recordings.values():
        if recording.status == RecordingStatus.RECORDING:
            return recording
    return None


recordings: dict[str, VideoRecordingFileset] = update_recordings_from_disk()
