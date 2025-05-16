import os
import json
import tempfile
import pytest
from rcam.events import JsonLinesEventRecorder, Event


def test_add_event_writes_json_line(tmp_path):
    filename = tmp_path / "events.jsonl"
    recorder = JsonLinesEventRecorder(str(filename))
    event = Event(name="test", code=1, frame=42, timestamp=123456, data={"foo": "bar"})
    recorder.add_event(event)
    recorder.close_file()

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1
    loaded = json.loads(lines[0])
    assert loaded["name"] == "test"
    assert loaded["code"] == 1
    assert loaded["frame"] == 42
    assert loaded["timestamp"] == 123456
    assert loaded["data"] == {"foo": "bar"}


def test_add_event_without_file_does_nothing(tmp_path):
    recorder = JsonLinesEventRecorder()
    event = Event(name="no_file", code=2, frame=0, timestamp=0, data={})
    # Should not raise
    recorder.add_event(event)


def test_begin_file_opens_file(tmp_path):
    filename = tmp_path / "begin.jsonl"
    recorder = JsonLinesEventRecorder()
    recorder.begin_file(str(filename))
    event = Event(name="begin", code=3, frame=1, timestamp=1, data={})
    recorder.add_event(event)
    recorder.close_file()
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1
    loaded = json.loads(lines[0])
    assert loaded["name"] == "begin"


def test_close_file_closes(tmp_path):
    filename = tmp_path / "close.jsonl"
    recorder = JsonLinesEventRecorder(str(filename))
    recorder.close_file()
    # Should not raise even if closed again
    recorder._file = None
    recorder.close_file()


def test_del_closes_file(tmp_path):
    filename = tmp_path / "del.jsonl"
    recorder = JsonLinesEventRecorder(str(filename))
    event = Event(name="del", code=4, frame=2, timestamp=2, data={})
    recorder.add_event(event)
    file_obj = recorder._file
    del recorder
    assert file_obj.closed
