import os

# constants to be chosen before startup
VIDEO_FILE_EXTENSION = "mp4"
METADATA_FILE_EXTENSION: str = "metadata.json"
EVENT_FILE_EXTENSION: str = "events.jsonl"

RECORDINGS_DIR = os.path.join(
    os.path.expanduser("~"), "Videos", "ImagingSourceRecorder"
)

if not os.path.exists(RECORDINGS_DIR):
    os.makedirs(RECORDINGS_DIR)
