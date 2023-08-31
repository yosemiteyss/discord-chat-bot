import logging
from json import dumps

import google.generativeai as palm

from typing import List

from src.constant.env import PALM_API_KEY
from src.service.chat_service import ChatService
from src.model.completion_data import CompletionData, CompletionResult
from src.model.conversation import Conversation
from src.model.message import Message
from src.model.model import Model
from src.model.prompt import Prompt

logger = logging.getLogger(__name__)


class PalmChatService(ChatService):
    def __init__(self):
        super().__init__()
        palm.configure(api_key=PALM_API_KEY)

    def get_model_list(self) -> List[Model]:
        return []

    def build_prompt(self, message: Message, history: List[Message]) -> Prompt:
        all_messages = [message for _ in history]
        all_messages = [x for x in all_messages if x is not None]
        all_messages.reverse()

        return Prompt(conversation=Conversation(all_messages))

    async def send_prompt(self, prompt: Prompt) -> CompletionData:
        rendered = prompt.render()
        logger.debug(dumps(rendered, indent=2, default=str))

        try:
            response = await palm.chat_async(messages=prompt.conversation.messages)
            # CompletionResult.OK
            return CompletionData(
                status=CompletionResult.OK,
                reply_text=response.last,
                status_text=None
            )
        except Exception as err:
            # CompletionResult.OTHER_ERROR
            logger.exception(err)
            return CompletionData(
                status=CompletionResult.OTHER_ERROR,
                reply_text=None,
                status_text=str(err)
            )

    def count_token_usage(self, messages: List[Message]) -> int:
        # TODO: implement count_token_usage
        pass
