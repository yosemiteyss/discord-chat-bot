import os
from typing import List

from dotenv import load_dotenv

from src.service.chat_service import ChatServiceType

load_dotenv()

CHAT_SERVICE = ChatServiceType(os.environ["CHAT_SERVICE"])

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_TYPE = os.environ.get("OPENAI_API_TYPE", None)
OPENAI_API_VERSION = os.environ.get("OPENAI_API_VERSION", None)

PALM_API_KEY = os.environ["PALM_API_KEY"]

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
DISCORD_CLIENT_ID = os.environ["DISCORD_CLIENT_ID"]
ALLOWED_SERVER_IDS: List[int] = [
    int(server_id) for server_id in os.environ["ALLOWED_SERVER_IDS"].split(",")
]

# Send Messages,
# Create Public Threads,
# Send Messages in Threads,
# Manage Messages,
# Manage Threads,
# Read Message History,
# Use Slash Command
BOT_INVITE_URL = os.environ["BOT_INVITE_URL"]
