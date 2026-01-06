import os
import uuid
import asyncio
import mimetypes

import config
from MediaLoom import api, app
from MediaLoom.core import core_func
from MediaLoom.core.mongo import filesdb

from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

# ----------------------------- CONSTANTS ----------------------------- #

ROOT = os.path.dirname(os.path.dirname(__file__))
TEMP_DIR = "temp"
CACHE_DIR = "static/files"
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "webp", "gif",
    "mp4", "mkv", "mov", "avi",
    "mp3", "wav", "ogg",
    "pdf", "zip", "rar"
}

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# ----------------------------- HEALTH CHECK ----------------------------- #

@api.get("/")
async def read_root():
    return {"status": "alive", "service": "MediaLoom"}

# ----------------------------- FRONTEND ----------------------------- #

@api.get("/medialoom")
def media_loom():
    return FileResponse(os.path.join(ROOT, "core", "index.html"))

# ----------------------------- UPLOAD MEDIA ----------------------------- #

@api.post("/upload", tags=["Media"])
async def upload_media(
    file: UploadFile = File(...),
    media_type: str = Form(...)
):
    if not file.filename:
        raise HTTPException(400, "Invalid file")

    ext = file.filename.rsplit(".", 1)[-1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported file type")

    temp_filename = f"{uuid.uuid4()}.{ext}"
    temp_path = os.path.join(TEMP_DIR, temp_filename)

    file_size = 0

    try:
        # -------- STREAM UPLOAD (RAM SAFE) -------- #
        with open(temp_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(413, "File too large")
                buffer.write(chunk)

        # -------- SEND TO TELEGRAM -------- #
        sent = await core_func.send_media(
            app,
            config.CHANNEL_ID,
            temp_path,
            media_type
        )

        if not sent:
            raise HTTPException(500, "Failed to upload to Telegram")

        # -------- SAVE TO DATABASE -------- #
        file_code = await filesdb.save_file(
            channel_id=config.CHANNEL_ID,
            media_id=sent.id,
            ext=ext,
            size=file_size
        )

        return {
            "status": "success",
            "link": f"{config.BASE_URL}/file/{file_code}.{ext}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ----------------------------- SERVE FILE ----------------------------- #

@api.get("/file/{file_name}", tags=["Media"])
async def serve_file(file_name: str):
    file_path = os.path.join(CACHE_DIR, file_name)

    try:
        # -------- CACHE MISS -------- #
        if not os.path.exists(file_path):
            file_code, ext = file_name.rsplit(".", 1)
            file_data = await filesdb.get_file(file_code)

            if not file_data:
                raise HTTPException(404, "File not found")

            msg = await app.get_messages(
                config.CHANNEL_ID,
                file_data["media_id"]
            )

            await app.download_media(
                msg,
                file_name=file_path
            )

        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"

        return FileResponse(
            path=file_path,
            media_type=mime_type,
            filename=file_name
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
