from dataclasses import dataclass

from fastapi.testclient import TestClient

import app.main as main_module


class FakeWord:
    def __init__(self, start: float, end: float, word: str, prob: float | None = 0.9) -> None:
        self.start = start
        self.end = end
        self.word = word
        self.probability = prob


class FakeSegment:
    def __init__(self) -> None:
        self.id = 0
        self.start = 0.0
        self.end = 1.0
        self.text = "hello"
        self.words = [FakeWord(0.0, 1.0, "hello", 0.95)]


@dataclass
class FakeInfo:
    language: str = "en"
    duration: float = 1.0


class FakeModel:
    def transcribe(self, path: str, word_timestamps: bool = True):  # noqa: FBT001, FBT002
        return [FakeSegment()], FakeInfo()


def test_transcribe_success(monkeypatch):
    # モデルをモックに差し替え
    monkeypatch.setattr(main_module, "model", FakeModel(), raising=True)

    client = TestClient(main_module.app)

    files = {"upload_file": ("sample.wav", b"RIFFDATA", "audio/wav")}
    resp = client.post("/transcribe", files=files)

    assert resp.status_code == 200
    data = resp.json()
    assert "info" in data and "segments" in data
    assert data["info"].get("language") == "en"
    assert len(data["segments"]) == 1
    seg0 = data["segments"][0]
    assert seg0["text"] == "hello"
    assert len(seg0["words"]) == 1
