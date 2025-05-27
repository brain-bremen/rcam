from dataclasses import dataclass
import json
from fastapi import FastAPI, HTTPException, Depends, Request
from rcam.events import Event
import rcam.config as config
from pydantic import BaseModel, HttpUrl
from typing import Callable, Dict
from fastapi.staticfiles import StaticFiles
from rcam.video_recorder_interface import MockVideoRecorder, VideoRecorderInterface
from rcam.video_recording_fileset import (
    VideoRecordingFileset,
    recording_id_from_video_filename,
)
import rcam.video_recordings_db as recordings_db
import os
import logging

PORT = 8000
HOST = "localhost"


def get_recorder(request: Request) -> VideoRecorderInterface:
    return request.app.state.recorder


def get_db(request: Request) -> recordings_db.SimpleDiskbasedVideoRecordingsDatabase:
    return request.app.state.db


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


class StartRecordingRequest(BaseModel):
    filename: str
    triggered_mode: bool = False
    metadata: Dict[str, str] = {}


class GetRecordingResponse(BaseModel):
    # recording_id: str
    recording: recordings_db.Recording
    urls: RecordingUrls
    metadata: dict

    @staticmethod
    def from_recording(recording: recordings_db.Recording):
        urls = RecordingUrls.from_fileset(recording.fileset)
        with open(recording.fileset.full_metadata_filename, "r") as file:
            metadata = json.load(file)
        return GetRecordingResponse(recording=recording, urls=urls, metadata=metadata)


# class StopRecordingRequest(BaseModel):
# recording_id: str


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


app = FastAPI()


@app.post("/recordings/current/event", response_model=AddEventResponse)
async def add_event(
    request: AddEventRequest,
    db: recordings_db.SimpleDiskbasedVideoRecordingsDatabase = Depends(get_db),
    recorder: VideoRecorderInterface = Depends(get_recorder),
):
    if db.is_recording_in_progress():
        logging.getLogger().error("No recording in progress")
        raise HTTPException(status_code=400, detail="No recording in progress")
    logging.getLogger().info(
        f"Event added via REST API: {request.event.name} at frame {request.event.frame}"
    )
    recorder.add_event(event=request.event)
    return {"message": "Event added"}


# Endpoints
@app.post("/recordings", response_model=GetRecordingResponse)
async def create_new_recording(
    request: StartRecordingRequest,
    recorder: VideoRecorderInterface = Depends(get_recorder),
    db: recordings_db.SimpleDiskbasedVideoRecordingsDatabase = Depends(get_db),
):
    if db.is_recording_in_progress():
        raise HTTPException(
            status_code=400, detail="A recording is already in progress"
        )

    # if filename has no extension add .mp4
    if "." not in request.filename:
        request.filename += f".{config.VIDEO_FILE_EXTENSION}"

    # make sure filename is a valid mp4 file
    if not request.filename.endswith(config.VIDEO_FILE_EXTENSION):
        raise HTTPException(
            status_code=400,
            detail=f"Filename must end with {config.VIDEO_FILE_EXTENSION}",
        )

    fileset = VideoRecordingFileset(
        recording_id=recording_id_from_video_filename(request.filename)
    )
    with open(fileset.full_metadata_filename, "w") as metadata_file:
        json.dump(request.metadata, metadata_file)

    recording = recordings_db.Recording(
        fileset=fileset,
        status=recordings_db.RecordingStatus.RECORDING,
    )
    db.add_recording(recording=recording)
    recorder.start_recording(
        recording_id=fileset.recording_id, triggered_mode=request.triggered_mode
    )
    logging.getLogger().info(
        f"Recording started with recording_id={fileset.recording_id}"
    )
    return GetRecordingResponse.from_recording(recording)


@app.post("/recordings/current/stop", response_model=StopRecordingResponse)
async def stop_recording(
    db: recordings_db.SimpleDiskbasedVideoRecordingsDatabase = Depends(get_db),
    recorder: VideoRecorderInterface = Depends(get_recorder),
):
    current_recording = recorder.get_current_recording()
    if current_recording is None:
        return {
            "message": "No recording stopped",
        }

    recorder.stop_recording()
    db.get_recording(
        current_recording.recording_id
    ).status = recordings_db.RecordingStatus.STOPPED
    logging.getLogger().info(
        f"Recording with recording_id={current_recording.recording_id} stopped"
    )

    return {
        "message": f"Recording with recording_id={current_recording.recording_id} stopped",
    }


@app.post("/recordings/current/metadata", response_model=AddMetadataResponse)
async def add_metadata(
    request: AddMetadataRequest,
    db: recordings_db.SimpleDiskbasedVideoRecordingsDatabase = Depends(get_db),
    recorder: VideoRecorderInterface = Depends(get_recorder),
):
    current_recording = db.get_current_recording()
    if current_recording is None:
        logging.getLogger().error("No recording in progress")
        raise HTTPException(status_code=404, detail="No recording in progress")
    recording = db.recordings[request.recording_id]
    with open(recording.fileset.full_metadata_filename, "a") as metadata_file:
        json.dump(request.metadata, metadata_file)
    logging.getLogger().info(
        f"Metadata added to recording {request.recording_id}: {request.metadata}"
    )
    return {"message": "Metadata added"}


@app.get("/recordings/current", response_model=GetRecordingResponse)
async def get_current_recording(
    db: recordings_db.SimpleDiskbasedVideoRecordingsDatabase = Depends(get_db),
):
    current_recording = db.get_current_recording()
    if current_recording is None:
        logging.getLogger().error("No recording in progress")
        raise HTTPException(status_code=404, detail="No recording in progress")
    return GetRecordingResponse.from_recording(current_recording)


@app.get("/recordings/{recording_id}", response_model=GetRecordingResponse)
async def get_recording(
    recording_id: str,
    db: recordings_db.SimpleDiskbasedVideoRecordingsDatabase = Depends(get_db),
):
    recording = db.get_recording(recording_id)
    if recording is None:
        logging.getLogger().error(f"Recording with ID {recording_id} not found")
        raise HTTPException(status_code=404, detail="Recording ID not found")
    return GetRecordingResponse.from_recording(recording)


@app.get("/recordings", response_model=list[str])
async def list_completed_recordings(
    db: recordings_db.SimpleDiskbasedVideoRecordingsDatabase = Depends(get_db),
):
    available_recordings = []
    logging.getLogger().debug("Listing completed recordings")
    for recording_id, recording in db.recordings.items():
        if recording.status == recordings_db.RecordingStatus.STOPPED:
            available_recordings.append(recording.fileset.recording_id)

    return available_recordings


# Mount static files route
app.mount("/files", StaticFiles(directory=config.RECORDINGS_DIR), name="files")


def run_http_server(
    recorder: VideoRecorderInterface,
    db: recordings_db.SimpleDiskbasedVideoRecordingsDatabase,
):
    import uvicorn

    app.state.recorder = recorder
    app.state.db = db
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    recorder = MockVideoRecorder()
    db = recordings_db.SimpleDiskbasedVideoRecordingsDatabase()
    run_http_server(recorder=recorder, db=db)
