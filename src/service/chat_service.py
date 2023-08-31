from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional

from src.service.azure_chat_service import AzureChatService
from src.service.openai_chat_service import OpenAIChatService
from src.service.palm_chat_service import PalmChatService
from src.model.completion_data import CompletionData
from src.model.message import Message
from src.model.model import Model
from src.model.prompt import Prompt


class ChatServiceType(Enum):
    OPENAI = 'openai'
    AZURE = 'azure'
    PALM = 'palm'


class ChatService(ABC):
    def __init__(self):
        # Set default model
        model_list = self.get_model_list()
        self.model = model_list[0] if model_list else None

    async def chat(self, message: Message, history: List[Message]) -> CompletionData:
        prompt = self.build_prompt(message, history)
        return await self.send_prompt(prompt)

    def set_model(self, model: Optional[Model]):
        self.model = model

    @abstractmethod
    def get_model_list(self) -> List[Model]:
        pass

    @abstractmethod
    def build_prompt(self, message: Message, history: List[Message]) -> Prompt:
        pass

    @abstractmethod
    async def send_prompt(self, prompt: Prompt) -> CompletionData:
        pass

    @abstractmethod
    def count_token_usage(self, messages: List[Message]) -> int:
        pass


class ChatServiceFactory:
    @staticmethod
    def get_service_cls(service_type: ChatServiceType) -> ChatService:
        if service_type == ChatServiceType.OPENAI:
            return OpenAIChatService()

        if service_type == ChatServiceType.AZURE:
            return AzureChatService()

        if service_type == ChatServiceType.PALM:
            return PalmChatService()

        raise ValueError(f'Unknown chat service type: {service_type}')
