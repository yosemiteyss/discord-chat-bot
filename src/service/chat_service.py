from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional

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
