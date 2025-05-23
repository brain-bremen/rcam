import os
import pytest
from fastapi.testclient import TestClient
from rcam.fastapi_http_server import app
from rcam import config
from rcam.video_recorder_interface import MockVideoRecorder
import rcam.video_recordings_db as recordings_db


app.state.db = recordings_db.SimpleDiskbasedVideoRecordingsDatabase()
app.state.recorder = MockVideoRecorder(app.state.db)
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Ensure the recordings directory exists and is empty

    # create temp directory for recordings
    config.RECORDINGS_DIR = os.path.join(
        os.path.expanduser("~"), "Videos", "RCam", "TMP"
    )

    if not os.path.exists(config.RECORDINGS_DIR):
        os.makedirs(config.RECORDINGS_DIR)

    yield
    # remove temp direcotry and all files
    for filename in os.listdir(config.RECORDINGS_DIR):
        file_path = os.path.join(config.RECORDINGS_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")


def test_start_recording():
    response = client.post(
        "/recordings",
        json={
            "filename": "test.mp4",
            "triggered_mode": False,
            "metadata": {"key": "value"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recording"]["fileset"]["recording_id"] == "test"
    assert data["recording"]["status"] == recordings_db.RecordingStatus.RECORDING.value
    assert data["metadata"] == {"key": "value"}
    assert len(data) == 3

    response = client.post(
        "/recordings",
        json={
            "filename": "test.mp4",
            "triggered_mode": False,
            "metadata": {"key": "value"},
        },
    )
    assert response.status_code == 400

    response = client.post("/recordings/current/stop")
    assert response.status_code == 200


def test_stop_recording():
    response = client.post(
        "/recordings", json={"filename": "test.mp4", "metadata": {"key": "value"}}
    )
    assert response.status_code == 200
    response = client.post("/recordings/current/stop", json={"recording_id": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Recording stopped"


def test_add_metadata():
    response = client.post(
        "/recordings/current/metadata",
        json={"recording_id": "test", "metadata": {"new_key": "new_value"}},
    )
    assert response.status_code == 404
    response = client.post(
        "/recordings", json={"filename": "test.mp4", "metadata": {"key": "value"}}
    )
    assert response.status_code == 200
    response = client.post(
        "/recordings/current/metadata",
        json={"recording_id": "test", "metadata": {"new_key": "new_value"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Metadata added"
    response = client.post("/recordings/current/stop", json={"recording_id": "test"})
    assert response.status_code == 200


def test_get_recording():
    recording_id = "test_id"
    response = client.post(
        "/recordings", json={"filename": recording_id, "metadata": {"key": "value"}}
    )
    assert response.status_code == 200
    response = client.post("/recordings/current/stop")
    assert response.status_code == 200
    response = client.get(f"/recordings/{recording_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["recording"]["fileset"]["recording_id"] == recording_id
    # assert data["recording_data"]["recording_id"] == "test"
    # assert data["status"] == RecordingStatus.STOPPED.value


def test_list_recordings():
    assert (
        client.post(
            "/recordings",
            json={"filename": "test1.mp4", "metadata": {"key1": "value1"}},
        ).status_code
        == 200
    )
    assert client.post("/recordings/current/stop").status_code == 200
    assert (
        client.post(
            "/recordings",
            json={"filename": "test2.mp4", "metadata": {"key2": "value2"}},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/recordings/current/stop", json={"recording_id": "test2"}
        ).status_code
        == 200
    )
    response = client.get("/recordings")
    assert response.status_code == 200
    data = response.json()
    assert "test1" in data
    assert "test2" in data
