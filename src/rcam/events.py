from abc import ABC, abstractmethod
import json
from dataclasses import dataclass
from typing import IO

logger = __import__("logging").getLogger(
    __name__
)  # Uses the global logging configuration


@dataclass
class Event:
    name: str
    code: int
    frame: int
    timestamp: int
    data: dict


class EventRecorderInterface(ABC):
    @abstractmethod
    def add_event(self, event: Event):
        pass

    @abstractmethod
    def begin_file(self, filename: str):
        pass

    @abstractmethod
    def close_file(self):
        pass


class JsonLinesEventRecorder(EventRecorderInterface):
    _file: IO | None

    def __init__(self, filename: str | None = None):
        if filename is not None:
            self._file = open(filename, "a", encoding="utf-8")
        else:
            self._file = None

    def begin_file(self, filename):
        self._file = open(filename, "a", encoding="utf-8")
        logger.info(f"Event recording started in file: {filename}")

    def close_file(self):
        if not self._file:
            return
        self._file.close()

    def add_event(self, event: Event):
        if self._file is None:
            return
        self._file.write(json.dumps(event.__dict__) + "\n")
        self._file.flush()
        logger.debug(f"Event added: {event.name} at frame {event.frame}")

    def __del__(self):
        if self._file:
            logger.info(f"Closing event recorder file {self._file}")
            self._file.close()
