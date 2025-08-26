import logging
import os
from dataclasses import asdict
from shutil import copyfileobj
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, UploadFile
from faster_whisper import WhisperModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


# モデルを起動時にロード（環境変数で調整可能）
MODEL_NAME = os.getenv("WHISPER_MODEL", "large-v3-turbo")
DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "float16")

logger.info(f"Loading model: {MODEL_NAME} on {DEVICE} ({COMPUTE_TYPE})")
model = WhisperModel(MODEL_NAME, device=DEVICE, compute_type=COMPUTE_TYPE)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "model": MODEL_NAME, "device": DEVICE}


@app.post("/transcribe")
def transcribe_audio(upload_file: UploadFile) -> Dict[str, Any]:
    temp_path = None
    try:
        with NamedTemporaryFile(delete=False, suffix=f"-{upload_file.filename}") as tmp:
            temp_path = tmp.name
            copyfileobj(upload_file.file, tmp)

        segments, info = model.transcribe(
            temp_path,
            word_timestamps=True,
        )

        segment_dicts: List[Dict[str, Any]] = []
        for seg in segments:
            segment_dicts.append(
                {
                    "id": seg.id,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "words": [
                        {
                            "start": w.start,
                            "end": w.end,
                            "word": w.word,
                            "prob": getattr(w, "probability", None),
                        }
                        for w in (seg.words or [])
                    ],
                }
            )

        return {"info": asdict(info), "segments": segment_dicts}
    except Exception as e:  # noqa: BLE001
        logger.exception("transcribe failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


