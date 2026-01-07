from config import MONGO_DB
from motor.motor_asyncio import AsyncIOMotorClient as MongoCli
import secrets

mongo = MongoCli(MONGO_DB)
db = mongo.FilesDB
collection = db.MediaData

# -------------------------------- Save File -------------------------------- #
async def save_file(channel_id, msg_id):
    file_id = secrets.token_hex(10)
    await collection.update_one(
        {"_id": file_id},
        {"$set": {"channel_id": channel_id, "media_id": msg_id}},
        upsert=True
    )
    return file_id


# -------------------------------- Get Fle -------------------------------- #
async def get_file(file_id):
    file = await collection.find_one({"_id": file_id})
    return file


# -------------------------------- Get All Files -------------------------------- #
async def get_all_files():
    files = await collection.find().to_list(length=0)
    return files
