from abc import ABC, abstractmethod
from os import PathLike
from datetime import datetime
from video_recording_fileset import VideoRecordingFileset
from pydantic.dataclasses import dataclass
from events import Event


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
