from dataclasses import asdict
from typing import Any


class TranscriptionService:
    def __init__(self, model: Any) -> None:
        self.model = model

    def transcribe_file(self, path: str, *, word_timestamps: bool = True) -> dict[str, Any]:
        segments, info = self.model.transcribe(path, word_timestamps=word_timestamps)

        segment_dicts: list[dict[str, Any]] = []
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


