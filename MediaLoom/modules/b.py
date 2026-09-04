import httpx, config
from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import RedirectResponse
from MediaLoom import api, app
from MediaLoom.core import core_func
from MediaLoom.core.mongo import filesdb

MAX_SIZE = 20 * 1024 * 1024  # 20MB Limit

@api.get("/")
async def root():
    return {"status": "alive", "service": "MediaLoom"}

@api.post("/upload", tags=["Media"])
async def upload_media(file: UploadFile = File(...), media_type: str = Form(...)):
    if not file.filename:
        raise HTTPException(400, "Invalid file")
    
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(413, "File exceeds 20MB preview limit")

    sent = await core_func.send_media_bytes(app, config.CHANNEL_ID, content, file.filename, media_type)
    if not sent:
        return {"status": "error", "message": "Telegram send failed"}

    file_code = await filesdb.save_file(config.CHANNEL_ID, sent.id)
    ext = file.filename.rsplit(".", 1)[-1].lower()
    return {"status": "success", "link": f"{config.BASE_URL}/file/{file_code}.{ext}"}

@api.get("/file/{file_name}")
async def serve_file(file_name: str):
    if any(char in file_name for char in ["..", "/", "\\"]) or "." not in file_name:
        raise HTTPException(400, "Invalid file name")

    file_code, _ = file_name.rsplit(".", 1)
    file_data = await filesdb.get_file(file_code)
    if not file_data:
        raise HTTPException(404, "File not found")

    msg = await app.get_messages(config.CHANNEL_ID, file_data["media_id"])
    media = msg.photo or msg.document or msg.video or msg.audio
    if not media:
        raise HTTPException(404, "Media not found")

    target = media[-1] if isinstance(media, list) else media
    if getattr(target, "file_size", 0) > MAX_SIZE:
        raise HTTPException(400, "File exceeds 20MB preview limit")

    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://api.telegram.org/bot{config.BOT_TOKEN}/getFile?file_id={target.file_id}")
        data = res.json()

    if not data.get("ok"):
        raise HTTPException(500, "Telegram API error")

    return RedirectResponse(f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{data['result']['file_path']}")
