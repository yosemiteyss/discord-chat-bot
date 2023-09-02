from typing import List, Any

import openai
from openai import ChatCompletion

from src.constant.env import AzureEnv
from src.constant.model import AZURE_MODELS
from src.service.openai_chat_service import OpenAIChatService
from src.model.model import Model


class AzureChatService(OpenAIChatService):
    def __init__(self):
        super().__init__()
        env = AzureEnv.load()
        openai.api_key = env.openai_api_key
        openai.api_base = env.openai_api_base
        openai.api_type = env.openai_api_type
        openai.api_version = env.openai_api_version

    def get_supported_models(self) -> List[Model]:
        return AZURE_MODELS

    async def create_chat_completion(self, rendered: List[dict[str, str]]) -> dict[str, Any]:
        # Use engine instead of model for azure.
        return await ChatCompletion.acreate(
            engine=self.model.name,
            messages=rendered
        )
