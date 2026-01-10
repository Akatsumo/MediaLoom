import config
from MediaLoom import app, BOT_NAME
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


buttons = InlineKeyboardMarkup([
                [
                  InlineKeyboardButton("🌐 Open WebApp", web_app=WebAppInfo(url="https://medialoom-d83dbabb0070.herokuapp.com/medialoom")
                )],[
                  InlineKeyboardButton("Repository", url="https://github.com/Akatsumo/MediaLoom")
                ]])


@app.on_message(filters.command("start"))
async def start(_, message):
    if message.chat.type == enums.ChatType.PRIVATE:
# if you want add photo replace this url  await message.reply_photo(photo="https://graph.org/file/371c915b8c97ecf62a2d6-edbae9f1a9a3ff4add.jpg",
        await message.reply_text(f"Hello, I'm {BOT_NAME}! I can host any type of media, including large files, with unlimited storage. Feel free to upload your files, and I'll take care of the rest!",
            reply_markup=buttons
        )
    else:
        await message.reply_text("I am Alive!!")

