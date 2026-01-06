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
async def upload_media(file: UploadFile = File(...), media_type: str = Form(...)):
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
        sent = await core_func.send_media(app, config.CHANNEL_ID, file.filename, media_type)
        if not sent:
            error_message = "Something went wrong while sending the file. Please contact the owner for assistance."
            return {"status": "error", "message": error_message}
            
        file_code = await filesdb.save_file(config.CHANNEL_ID, sent.id, ext)
        link = f"{config.BASE_URL}/file/{file_code}.{ext}"
        os.remove(file.filename)
        return {"status": "success", "link": link}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

# ----------------------------- SERVE FILE ----------------------------- #

@api.get("/file/{file_name}")
async def serve_file(file_name: str):
    try:
        save_folder = "static/files"
        os.makedirs(save_folder, exist_ok=True)

        file_path = os.path.join(save_folder, file_name)

        if not os.path.exists(file_path):
            file_code, ext = file_name.rsplit(".", 1)
            file_data = await filesdb.get_file(file_code)
            if not file_data:
                raise HTTPException(status_code=404, detail="File not found in database.")

            msg = await app.get_messages(config.CHANNEL_ID, file_data["media_id"])
            downloaded_path = await asyncio.create_task(app.download_media(msg, file_name=file_path))

            if not os.path.exists(downloaded_path):
                raise HTTPException(status_code=500, detail="Failed to download file from Telegram.")

        file_size = os.path.getsize(file_path)
        ext = file_name.split(".")[-1].lower()

        if ext in ["mp4", "mkv", "mov", "avi"]:
            media_type = f"video/{ext if ext != 'mkv' else 'x-matroska'}"
        elif ext in ["jpg", "jpeg", "png", "gif", "webp"]:
            media_type = f"image/{ext}"
        elif ext == "pdf":
            media_type = "application/pdf"
        else:
            media_type = "application/octet-stream"

        if media_type.startswith("video/") and file_size > 50 * 1024 * 1024:
            return FileResponse(
                file_path,
                media_type="application/octet-stream",
                filename=file_name,
                headers={"Content-Disposition": f"attachment; filename={file_name}"}
            )

        return FileResponse(file_path, media_type=media_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
