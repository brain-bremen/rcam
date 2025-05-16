from dataclasses import dataclass
import os
from config import VIDEO_FILE_EXTENSION, METADATA_FILE_EXTENSION, EVENT_FILE_EXTENSION
import config


def recording_id_from_video_filename(filename: str) -> str:
    return filename[:-4]


@dataclass
class VideoRecordingFileset:
    """Collection of files representing one video recording"""

    recording_id: str  # basename without extension

    @property
    def video_filename(self) -> str:
        return f"{self.recording_id}.{VIDEO_FILE_EXTENSION}"

    @property
    def full_video_filename(self) -> str:
        return os.path.join(config.RECORDINGS_DIR, self.video_filename)

    @property
    def metadata_filename(self) -> str:
        return f"{self.recording_id}.{METADATA_FILE_EXTENSION}"

    @property
    def full_metadata_filename(self) -> str:
        return os.path.join(config.RECORDINGS_DIR, self.metadata_filename)

    @property
    def event_filename(self) -> str:
        return f"{self.recording_id}.{EVENT_FILE_EXTENSION}"

    @property
    def full_event_filename(self) -> str:
        return os.path.join(config.RECORDINGS_DIR, self.event_filename)

    def exists(self) -> bool:
        """Check if all files exists"""
        if not self.all_files_are_present:
            return False

        return (
            os.path.exists(self.full_video_filename)
            and os.path.exists(self.full_metadata_filename)
            and os.path.exists(self.full_event_filename)
        )

    def __str__(self) -> str:
        return (
            f"{self.recording_id}\n"
            f"├── {self.video_filename}\n"
            f"├── {self.metadata_filename}\n"
            f"└── {self.event_filename}"
        )
