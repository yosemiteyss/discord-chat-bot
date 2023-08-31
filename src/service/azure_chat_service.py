from typing import List, Any

from openai import ChatCompletion

from src.constant.model import AZURE_MODELS
from src.service.openai_chat_service import OpenAIChatService
from src.model.model import Model


class AzureChatService(OpenAIChatService):
    def get_model_list(self) -> List[Model]:
        return AZURE_MODELS

    async def create_chat_completion(self, rendered: List[dict[str, str]]) -> dict[str, Any]:
        # Use engine instead of model for azure.
        return await ChatCompletion.acreate(
            engine=self.model.name,
            messages=rendered
        )
