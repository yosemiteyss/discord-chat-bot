import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class CommonEnv:
    chat_service: str
    discord_bot_token: str
    discord_client_id: str
    allow_server_ids: List[int]
    bot_invite_url: str

    @staticmethod
    def load() -> "CommonEnv":
        return CommonEnv(
            chat_service=os.environ["CHAT_SERVICE"],
            discord_bot_token=os.environ["DISCORD_BOT_TOKEN"],
            discord_client_id=os.environ["DISCORD_CLIENT_ID"],
            allow_server_ids=[
                int(server_id) for server_id in os.environ["ALLOWED_SERVER_IDS"].split(",")
            ],
            bot_invite_url=os.environ["BOT_INVITE_URL"],
        )


@dataclass(frozen=True)
class OpenAIEnv:
    openai_api_key: str

    @staticmethod
    def load() -> "OpenAIEnv":
        return OpenAIEnv(
            openai_api_key=os.environ["OPENAI_API_KEY"],
        )


@dataclass(frozen=True)
class AzureOpenAIEnv:
    openai_api_key: str
    openai_api_base: str
    openai_api_version: str

    @staticmethod
    def load() -> "AzureOpenAIEnv":
        return AzureOpenAIEnv(
            openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
            openai_api_base=os.environ["AZURE_OPENAI_API_BASE"],
            openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        )


@dataclass(frozen=True)
class PalmEnv:
    palm_api_key: str

    @staticmethod
    def load() -> "PalmEnv":
        return PalmEnv(
            palm_api_key=os.environ["PALM_API_KEY"],
        )
