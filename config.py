from os import getenv

API_ID = int(getenv("API_ID", "26850449"))
API_HASH = getenv("API_HASH", "72a730c380e68095a8549ad7341b0608")
BOT_TOKEN = getenv("BOT_TOKEN", "")
BASE_URL = getenv("BASE_URL", "")
OWNER_ID = list(map(int, getenv("OWNER_ID", "8462359928").split()))
CHANNEL_ID = int(getenv("CHANNEL_ID", ""))
MONGO_DB = getenv("MONGO_DB", "")
