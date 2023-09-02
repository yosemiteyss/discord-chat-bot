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
        self.init_env()

        # Set default model
        model_list = self.get_supported_models()
        self.model = model_list[0] if model_list else None

    def init_env(self):
        """Initialize environment variables required for chat service."""

    async def chat(self, history: List[Optional[Message]]) -> CompletionData:
        """Send conversation history to chat service and return response. Messages are in chronological order."""
        prompt = self.build_prompt(history)
        return await self.send_prompt(prompt)

    def set_current_model(self, model: Optional[Model]):
        """Set current active model."""
        self.model = model

    @abstractmethod
    def get_supported_models(self) -> List[Model]:
        """Return a list of supported models."""

    @abstractmethod
    def build_system_message(self) -> Message:
        """Return a system message to be sent to the chat service."""

    @abstractmethod
    def build_prompt(self, history: List[Optional[Message]]) -> Prompt:
        """Convert conversation history to prompt."""

    @abstractmethod
    def render_prompt(self, prompt: Prompt) -> List[dict[str, str]]:
        """Convert prompt to json structure."""

    @abstractmethod
    def render_message(self, message: Message) -> dict[str, str]:
        """Convert message to json structure."""

    @abstractmethod
    async def send_prompt(self, prompt: Prompt) -> CompletionData:
        """Send prompt to chat service and return response."""

    @abstractmethod
    def count_token_usage(self, messages: List[Message]) -> int:
        """Return the number of tokens used by the messages."""
