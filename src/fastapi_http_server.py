import json
from fastapi import FastAPI, HTTPException
from events import Event
from pydantic import BaseModel
from typing import Callable, Dict
from fastapi.staticfiles import StaticFiles
from video_recorder_interface import (
    RECORDINGS_DIR,
    VideoRecordingFileset,
    recording_id_from_video_filename,
)
import video_recordings_db as db
import os

PORT = 8000
HOST = "localhost"


def url_from_filename(filename: str | None) -> str | None:
    if filename is None:
        return None
    # strip folder from filename
    filename = os.path.basename(filename)
    return f"http://{HOST}:{PORT}/files/{filename}"


app = FastAPI()


# Data models
class StartRecordingRequest(BaseModel):
    filename: str
    metadata: Dict[str, str] = {}


class StopRecordingRequest(BaseModel):
    recording_id: str


class StopRecordingResponse(BaseModel):
    message: str
    recording: Recording


class AddMetadataRequest(BaseModel):
    recording_id: str
    metadata: Dict[str, str]


class AddEventRequest(BaseModel):
    event: Event


class AddEventResponse(BaseModel):
    message: str


class AddMetadataResponse(BaseModel):
    message: str


class RecordingResponse(BaseModel):
    recording_id: str
    filename: str
    metadata: Dict[str, str]
    file_url: str


def start_recording_func(filename: str) -> None:
    return None


def stop_recording_func() -> None:
    return None


def add_event_func(event: Event) -> None:
    return None


@app.post("/recordings/current/event", response_model=AddEventResponse)
async def add_event(request: AddEventRequest):
    if not any(
        recording.status == db.RecordingStatus.RECORDING
        for recording in db.recordings.values()
    ):
        raise HTTPException(status_code=400, detail="No recording in progress")
    add_event_func(request.event)
    return {"message": "Event added"}


# Endpoints
@app.post("/recordings", response_model=Recording)
async def create_new_recording(request: StartRecordingRequest):
    if any(
        recording.status == db.RecordingStatus.RECORDING
        for recording in db.recordings.values()
    ):
        raise HTTPException(
            status_code=400, detail="A recording is already in progress"
        )

    # if filename has no extension add .mp4
    if "." not in request.filename:
        request.filename += ".mp4"

    # make sure filename is a valid mp4 file
    if not request.filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Filename must end with .mp4")

    dataset = VideoRecordingFileset(
        recording_id=recording_id_from_video_filename(request.filename)
    )
    with open(
        os.path.join(RECORDINGS_DIR, dataset.metadata_filename), "w"
    ) as metadata_file:
        json.dump(request.metadata, metadata_file)

    recordings[dataset.recording_id] = Recording(
        recording_data=dataset,
        status=RecordingStatus.RECORDING,
        video_url=url_from_filename(request.filename),
        metadata_url=url_from_filename(dataset.metadata_filename),
        event_url=url_from_filename(dataset.event_filename),
    )
    start_recording_func(request.filename)

    return recordings[dataset.recording_id]


@app.post("/recordings/stop", response_model=StopRecordingResponse)
async def stop_recording(request: StopRecordingRequest):
    if request.recording_id not in recordings:
        raise HTTPException(status_code=404, detail="Recording ID not found")
    recordings[request.recording_id].status = RecordingStatus.STOPPED

    stop_recording_func()

    return {
        "message": "Recording stopped",
        "recording": recordings[request.recording_id],
    }


@app.post("/recordings/current/metadata", response_model=AddMetadataResponse)
async def add_metadata(request: AddMetadataRequest):
    if request.recording_id not in recordings:
        raise HTTPException(status_code=404, detail="Recording ID not found")
    recording = recordings[request.recording_id]
    with open(
        os.path.join(RECORDINGS_DIR, recording.recording_data.metadata_filename), "w"
    ) as metadata_file:
        json.dump(request.metadata, metadata_file)
    return {"message": "Metadata added"}


@app.get("/recordings/current", response_model=Recording)
async def get_current_recording():
    raise HTTPException(status_code=404, detail="Not implemented yet")


@app.get("/recordings/{recording_id}", response_model=Recording)
async def get_recording(recording_id: str):
    if recording_id not in recordings:
        raise HTTPException(status_code=404, detail="Recording ID not found")
    recording = recordings[recording_id]
    if recording.status != RecordingStatus.STOPPED:
        raise HTTPException(status_code=400, detail="Recording is not yet stopped")
    return recordings[recording_id]


@app.get("/recordings", response_model=Dict[str, Recording])
async def list_recordings():
    available_recordings = {}
    # update_recordings_from_disk()

    for recording_id, recording in recordings.items():
        if recording.status == RecordingStatus.STOPPED:
            available_recordings[recording_id] = recording

    return available_recordings


# Mount static files route
app.mount("/files", StaticFiles(directory=RECORDINGS_DIR), name="files")


def run_http_server(
    start_func: Callable[[str], None],
    stop_func: Callable[[], None],
    event_func: Callable[[Event], None],
):
    global start_recording_func, stop_recording_func, add_event_func
    start_recording_func = start_func
    stop_recording_func = stop_func
    add_event_func = event_func
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    run_http_server(start_recording_func, stop_recording_func, add_event_func)
