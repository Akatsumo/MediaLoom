import os
import uuid
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
BASE_DIR = "static/files"
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(BASE_DIR, exist_ok=True)

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
    temp_filename = f"{uuid.uuid4()}.{ext}"
    temp_path = os.path.join(TEMP_DIR, temp_filename)
    file_size = 0

    try:
        with open(temp_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(413, "File too large")
                buffer.write(chunk)

        sent = await core_func.send_media(app, config.CHANNEL_ID, temp_path, media_type)
        if not sent:
            return {"status": "error", "message": "Something went wrong while sending the file. Please contact the owner for assistance."}

        file_code = await filesdb.save_file(config.CHANNEL_ID, sent.id)
        link = f"{config.BASE_URL}/file/{file_code}.{ext}"

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {"status": "success", "link": link}

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"status": "error", "message": str(e)}


# ----------------------------- SERVE FILE ----------------------------- #
@api.get("/file/{file_name}")
async def serve_file(file_name: str):
    try:
        if ".." in file_name or "/" in file_name or "\\" in file_name:
            raise HTTPException(status_code=400, detail="Invalid file name")

        file_path = os.path.join(BASE_DIR, file_name)

        if not os.path.exists(file_path):
            if "." not in file_name:
                raise HTTPException(status_code=400, detail="Invalid file format")

            file_code, _ = file_name.rsplit(".", 1)
            file_data = await filesdb.get_file(file_code)

            if not file_data:
                raise HTTPException(status_code=404, detail="File not found")

            msg = await app.get_messages(
                config.CHANNEL_ID,
                file_data["media_id"]
            )

            downloaded_path = await app.download_media(
                msg,
                file_name=file_path
            )

            if not downloaded_path or not os.path.exists(downloaded_path):
                raise HTTPException(status_code=500, detail="Telegram download failed")

        file_size = os.path.getsize(file_path)

        media_type, _ = mimetypes.guess_type(file_path)
        media_type = media_type or "application/octet-stream"

        if media_type.startswith("video/") and file_size > 50 * 1024 * 1024:
            return FileResponse(
                file_path,
                media_type="application/octet-stream",
                filename=file_name,
                headers={
                    "Content-Disposition": f'attachment; filename="{file_name}"'
                }
            )

        return FileResponse(
            file_path,
            media_type=media_type,
            filename=file_name
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )




