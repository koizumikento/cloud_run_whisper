import logging
import os
from shutil import copyfileobj
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile
from faster_whisper import WhisperModel
from pydantic import BaseModel

from .settings import settings
from .services.transcription_service import TranscriptionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


# Pydantic response models
class HealthResponse(BaseModel):
    status: str
    model: str
    device: str


class Word(BaseModel):
    start: float
    end: float
    word: str
    prob: float | None = None


class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: list[Word]


class TranscribeResponse(BaseModel):
    info: dict[str, Any]
    segments: list[Segment]


# モデルを起動時にロード（pydantic-settings で管理）
if settings.whisper_skip_load:
    logger.info("Skipping Whisper model load (WHISPER_SKIP_LOAD=1)")
    model = None
else:
    logger.info(
        "Loading model: %s on %s (%s)",
        settings.whisper_model,
        settings.whisper_device,
        settings.whisper_compute_type,
    )
    model = WhisperModel(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return {"status": "ok", "model": settings.whisper_model, "device": settings.whisper_device}


@app.post("/transcribe", response_model=TranscribeResponse)
def transcribe_audio(upload_file: UploadFile) -> TranscribeResponse:
    temp_path = None
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        with NamedTemporaryFile(delete=False, suffix=f"-{upload_file.filename}") as tmp:
            temp_path = tmp.name
            copyfileobj(upload_file.file, tmp)

        service = TranscriptionService(model)
        return service.transcribe_file(temp_path, word_timestamps=True)
    except Exception as e:  # noqa: BLE001
        logger.exception("transcribe failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
