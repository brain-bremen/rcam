from abc import ABC, abstractmethod
from os import PathLike
import os
from datetime import datetime

# from dataclasses import dataclass
from pydantic.dataclasses import dataclass
from event_recorder import Event

RECORDINGS_DIR = os.path.join(os.path.expanduser("~"), "Documents", "recordings")


@dataclass
class RecordingMetadata:
    start_time: datetime
    end_time: datetime


class RecorderSettings(ABC):
    pass


def recording_id_from_video_filename(filename: str) -> str:
    return filename[:-4]


@dataclass
class RecordingDataset:
    """Collection of files representing one video recording"""

    recording_id: str  # basename without extension
    recordings_folder: str = RECORDINGS_DIR
    video_extension: str = "mp4"
    metadata_extension: str = "metadata.json"
    event_extension: str = "events.jsonl"

    @property
    def video_filename(self) -> str | None:
        return f"{self.recording_id}.{self.video_extension}"

    @property
    def metadata_filename(self) -> str:
        return f"{self.recording_id}.{self.metadata_extension}"

    @property
    def event_filename(self) -> str | None:
        return f"{self.recording_id}.{self.event_extension}"

    @property
    def all_files_are_present(self) -> bool:
        """Check if all files are present"""
        return (
            self.video_filename is not None
            and self.metadata_filename is not None
            and self.event_filename is not None
        )


class VideoRecorderInterface(ABC):
    @abstractmethod
    def start_recording(
        self,
        file_name: str | PathLike,
        frame_rate: float | None = None,
        triggered_mode: bool = False,
        settings: RecorderSettings | None = None,
    ):
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
