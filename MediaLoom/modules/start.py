from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from MediaLoom import app, BOT_NAME


buttons = InlineKeyboardMarkup([
                [
                  InlineKeyboardButton("Website", url="https://medialoom-d83dbabb0070.herokuapp.com/medialoom")
                ],[
                  InlineKeyboardButton("Repository", url="https://github.com/Akatsumo/MediaLoom")
                ]])

@app.on_message(filters.command("start"))
async def start_(_, message):
  # if you want add photo replace this url  await message.reply_photo(photo="https://graph.org/file/371c915b8c97ecf62a2d6-edbae9f1a9a3ff4add.jpg",
    await message.reply_text(f"Hello, I'm {BOT_NAME}! I can host any type of media, including large files, with unlimited storage.Feel free to upload your files, and I'll take care of the rest!",
        reply_markup=buttons
    )
