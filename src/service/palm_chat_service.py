import logging
from json import dumps
from typing import List

import google.generativeai as palm

from src.constant.env import PalmEnv
from src.model.role import Role
from src.service.chat_service import ChatService
from src.model.completion_data import CompletionData, CompletionResult
from src.model.message import Message
from src.model.model import Model
from src.model.prompt import Prompt

logger = logging.getLogger(__name__)


class PalmChatService(ChatService):
    def __init__(self):
        super().__init__()
        env = PalmEnv.load()
        palm.configure(api_key=env.palm_api_key)

    def get_supported_models(self) -> List[Model]:
        return []

    def build_system_message(self) -> Message:
        return Message(
            role=Role.SYSTEM.value,
            content="You are Palm, a large language model trained by Google. Your job is to answer questions "
                    "accurately and provide detailed example."
        )

    def build_prompt(self, history: List[Message]) -> Prompt:
        sys_message = self.build_system_message()
        all_messages = [x for x in history if x is not None]
        return Prompt(conversation=all_messages, header=sys_message)

    def render_prompt(self, prompt: Prompt) -> List[dict[str, str]]:
        messages = [self.render_message(message) for message in prompt.conversation]
        return messages

    def render_message(self, message: Message) -> dict[str, str]:
        # Request format:
        # [
        #   {'author': '0', 'content': 'Hello'},
        #   {'author': '1', 'content': 'Hi there! How can I help you today?'},
        #   {'author': '0', 'content': "Just chillin'"}
        # ]
        rendered = {
            "author": "0" if message.role == Role.USER.value else "1",
            "content": message.content
        }
        return {k: v for k, v in rendered.items() if v is not None}

    async def send_prompt(self, prompt: Prompt) -> CompletionData:
        rendered_prompt = prompt.render()
        logger.debug(dumps(rendered_prompt, indent=2, default=str))

        try:
            response = await palm.chat_async(context=prompt.header.content, messages=rendered_prompt)

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
        return -1
