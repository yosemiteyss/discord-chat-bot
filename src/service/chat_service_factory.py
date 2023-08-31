from src.service.azure_chat_service import AzureChatService
from src.service.chat_service import ChatServiceType, ChatService
from src.service.openai_chat_service import OpenAIChatService
from src.service.palm_chat_service import PalmChatService


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
