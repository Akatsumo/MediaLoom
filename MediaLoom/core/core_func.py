
# ------------------------- Send Media -------------------------#
async def send_media(app, channel_id, file_path, media_type):
    try:
        if media_type.startswith("image/"):
            if media_type == "image/gif":
                sent = await app.send_animation(channel_id, animation=file_path)
            else:
                sent = await app.send_photo(channel_id, photo=file_path)
                
        elif media_type.startswith("video/"):
            sent = await app.send_video(channel_id, video=file_path)
            
        elif media_type.startswith("audio/"):
            sent = await app.send_audio(channel_id, audio=file_path)

        elif media_type == "application/pdf":
            sent = await app.send_document(channel_id, document=file_path)

        else:
            sent = await app.send_document(channel_id, document=file_path)
        return sent
    except Exception as e:
        print(f"[SEND_MEDIA_ERROR] {e}")
        return None





