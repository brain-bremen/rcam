from dataclasses import dataclass
import json
from fastapi import FastAPI, HTTPException
from imaging_source_recorder.events import Event
import imaging_source_recorder.config as config
from pydantic import BaseModel, HttpUrl
from typing import Callable, Dict
from fastapi.staticfiles import StaticFiles
from imaging_source_recorder.video_recording_fileset import (
    VIDEO_FILE_EXTENSION,
    VideoRecordingFileset,
    recording_id_from_video_filename,
)
import imaging_source_recorder.video_recordings_db as db
import os

PORT = 8000
HOST = "localhost"


def url_from_filename(filename: str) -> HttpUrl:
    if filename is None:
        return None
    # strip folder from filename
    filename = os.path.basename(filename)
    return HttpUrl(f"http://{HOST}:{PORT}/files/{filename}")


@dataclass
class RecordingUrls:
    video_file_url: HttpUrl
    metadata_file_url: HttpUrl
    event_file_url: HttpUrl

    @staticmethod
    def from_fileset(fileset: VideoRecordingFileset):
        return RecordingUrls(
            video_file_url=url_from_filename(fileset.video_filename),
            metadata_file_url=url_from_filename(fileset.metadata_filename),
            event_file_url=url_from_filename(fileset.event_filename),
        )


app = FastAPI()


# Data models
class StartRecordingRequest(BaseModel):
    filename: str
    metadata: Dict[str, str] = {}


class GetRecordingResponse(BaseModel):
    recording_id: str
    recording: db.Recording
    urls: RecordingUrls
    metadata: str


class StopRecordingRequest(BaseModel):
    recording_id: str


class StopRecordingResponse(BaseModel):
    message: str


class AddMetadataRequest(BaseModel):
    recording_id: str
    metadata: Dict[str, str]


class AddEventRequest(BaseModel):
    event: Event


class AddEventResponse(BaseModel):
    message: str


class AddMetadataResponse(BaseModel):
    message: str


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
@app.post("/recordings", response_model=GetRecordingResponse)
async def create_new_recording(request: StartRecordingRequest):
    if db.is_recording_in_progress():
        raise HTTPException(
            status_code=400, detail="A recording is already in progress"
        )

    # if filename has no extension add .mp4
    if "." not in request.filename:
        request.filename += VIDEO_FILE_EXTENSION

    # make sure filename is a valid mp4 file
    if not request.filename.endswith(VIDEO_FILE_EXTENSION):
        raise HTTPException(
            status_code=400, detail=f"Filename must end with {VIDEO_FILE_EXTENSION}"
        )

    dataset = VideoRecordingFileset(
        recording_id=recording_id_from_video_filename(request.filename)
    )
    with open(
        os.path.join(db.RECORDINGS_DIR, dataset.metadata_filename), "w"
    ) as metadata_file:
        json.dump(request.metadata, metadata_file)

    db.recordings[dataset.recording_id] = db.Recording(
        fileset=dataset,
        status=db.RecordingStatus.RECORDING,
    )
    start_recording_func(request.filename)

    return db.recordings[dataset.recording_id]


@app.post("/recordings/stop", response_model=StopRecordingResponse)
async def stop_recording(request: StopRecordingRequest):
    if request.recording_id not in db.recordings:
        raise HTTPException(status_code=404, detail="Recording ID not found")
    db.recordings[request.recording_id].status = db.RecordingStatus.STOPPED

    stop_recording_func()

    return {
        "message": f"Recording {request.recording_id} stopped",
    }


@app.post("/recordings/current/metadata", response_model=AddMetadataResponse)
async def add_metadata(request: AddMetadataRequest):
    if request.recording_id not in db.recordings:
        raise HTTPException(status_code=404, detail="Recording ID not found")
    recording = db.recordings[request.recording_id]
    with open(recording.fileset.full_metadata_filename, "a") as metadata_file:
        json.dump(request.metadata, metadata_file)
    return {"message": "Metadata added"}


@app.get("/recordings/current", response_model=GetRecordingResponse)
async def get_current_recording():
    current_recording = db.get_current_recording()
    if current_recording is None:
        raise HTTPException(status_code=404, detail="No recording in progress")
    urls = RecordingUrls.from_fileset(current_recording.fileset)
    with open(current_recording.fileset.full_metadata_filename, "r") as file:
        metadata = json.load(file)
    metadata = metadata
    return GetRecordingResponse(
        recording_id=current_recording.fileset.recording_id,
        recording=current_recording,
        urls=urls,
        metadata=metadata,
    )


@app.get("/recordings/{recording_id}", response_model=GetRecordingResponse)
async def get_recording(recording_id: str):
    if recording_id not in db.recordings:
        raise HTTPException(status_code=404, detail="Recording ID not found")
    recording = db.recordings[recording_id]

    urls = RecordingUrls.from_fileset(recording.fileset)
    with open(recording.fileset.full_metadata_filename, "r") as file:
        metadata = json.load(file)
    metadata = metadata
    return GetRecordingResponse(
        recording_id=recording.fileset.recording_id,
        recording=recording,
        urls=urls,
        metadata=metadata,
    )


@app.get("/recordings", response_model=list[str])
async def list_completed_recordings():
    available_recordings = []
    # update_recordings_from_disk()

    for recording_id, recording in db.recordings.items():
        if recording.status == db.RecordingStatus.STOPPED:
            available_recordings.append(recording.fileset.recording_id)

    return available_recordings


# Mount static files route
app.mount("/files", StaticFiles(directory=config.RECORDINGS_DIR), name="files")


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
