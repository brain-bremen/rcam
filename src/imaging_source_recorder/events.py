from abc import ABC, abstractmethod
import json
from dataclasses import dataclass
from typing import IO


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

    def close_file(self):
        if not self._file:
            return
        self._file.close()

    def add_event(self, event: Event):
        if self._file is None:
            return
        self._file.write(json.dumps(event.__dict__) + "\n")
        self._file.flush()

    def __del__(self):
        if self._file:
            self._file.close()
