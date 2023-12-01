from typing import List, Any

from openai.lib.azure import AsyncAzureOpenAI

from src.constant.env import AzureOpenAIEnv
from src.constant.model import AZURE_MODELS
from src.service.openai_service import OpenAIService
from src.model.model import Model


class AzureOpenAIService(OpenAIService):
    client: AsyncAzureOpenAI

    def init_env(self):
        env = AzureOpenAIEnv.load()
        self.client = AsyncAzureOpenAI(
            api_key=env.openai_api_key,
            api_version=env.openai_api_version,
            azure_endpoint=env.openai_api_base
        )

    def get_supported_models(self) -> List[Model]:
        return AZURE_MODELS

    async def create_chat_completion(self, rendered: List[dict[str, str]]) -> dict[str, Any]:
        chat_completion = await self.client.chat.completions.create(
            model=self.model.name,
            messages=rendered
        )
        return vars(chat_completion)
