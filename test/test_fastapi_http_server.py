import os
import json
import pytest
from fastapi.testclient import TestClient
from fastapi_http_server import app, RECORDINGS_DIR, RecordingStatus, recordings

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Ensure the recordings directory exists and is empty
    if not os.path.exists(RECORDINGS_DIR):
        os.makedirs(RECORDINGS_DIR)
    else:
        for filename in os.listdir(RECORDINGS_DIR):
            file_path = os.path.join(RECORDINGS_DIR, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)

    # Teardown: Clear the recordings dictionary
    yield
    recordings.clear()


def test_start_recording():
    response = client.post(
        "/recordings/start", json={"filename": "test.mp4", "metadata": {"key": "value"}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recording_data"]["recording_id"] == "test"
    assert data["status"] == RecordingStatus.RECORDING.value
    # assert data["metadata"] == {"key": "value"}


def test_stop_recording():
    client.post(
        "/recordings/start", json={"filename": "test.mp4", "metadata": {"key": "value"}}
    )
    response = client.post("/recordings/stop", json={"recording_id": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Recording stopped"
    assert data["recording"]["status"] == RecordingStatus.STOPPED.value


def test_add_metadata():
    client.post(
        "/recordings/start", json={"filename": "test.mp4", "metadata": {"key": "value"}}
    )
    response = client.post(
        "/recordings/metadata",
        json={"recording_id": "test", "metadata": {"new_key": "new_value"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Metadata added"
    # assert recordings["test"].metadata == {"new_key": "new_value"}


def test_get_recording():
    client.post(
        "/recordings/start", json={"filename": "test.mp4", "metadata": {"key": "value"}}
    )
    client.post("/recordings/stop", json={"recording_id": "test"})
    response = client.get("/recordings/test")
    assert response.status_code == 200
    data = response.json()
    assert data["recording_data"]["recording_id"] == "test"
    assert data["status"] == RecordingStatus.STOPPED.value


def test_list_recordings():
    client.post(
        "/recordings/start",
        json={"filename": "test1.mp4", "metadata": {"key1": "value1"}},
    )
    client.post("/recordings/stop", json={"recording_id": "test1"})
    client.post(
        "/recordings/start",
        json={"filename": "test2.mp4", "metadata": {"key2": "value2"}},
    )
    client.post("/recordings/stop", json={"recording_id": "test2"})
    response = client.get("/recordings")
    assert response.status_code == 200
    data = response.json()
    assert "test1" in data
    assert "test2" in data
    assert data["test1"]["status"] == RecordingStatus.STOPPED.value
    assert data["test2"]["status"] == RecordingStatus.STOPPED.value
