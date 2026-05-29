from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from asr_md.core import AsrToMarkdownConverter

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "runtime" / "uploads"

app = FastAPI(title="语音转 md 本地服务", version="0.1.0")
converter = AsrToMarkdownConverter()

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> Dict[str, Any]:
    data = converter.health()
    data["status"] = "ok"
    return data


@app.post("/api/transcribe")
async def transcribe(audio_file: UploadFile = File(...)) -> Dict[str, Any]:
    suffix = Path(audio_file.filename or "audio.wav").suffix or ".wav"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    upload_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    try:
        with upload_path.open("wb") as target:
            shutil.copyfileobj(audio_file.file, target)
        return converter.transcribe_to_markdown(upload_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        try:
            upload_path.unlink(missing_ok=True)
        except OSError:
            pass
