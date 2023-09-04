import logging
from asyncio import to_thread

from json import dumps
from typing import List, Optional

import google.generativeai as palm

from src.constant.env import PalmEnv
from src.constant.model import PALM_MODELS
from src.model.role import Role
from src.service.chat_service import ChatService
from src.model.completion_data import CompletionData, CompletionResult
from src.model.message import Message
from src.model.model import Model
from src.model.prompt import Prompt

logger = logging.getLogger(__name__)


class PalmService(ChatService):
    def init_env(self):
        env = PalmEnv.load()
        palm.configure(api_key=env.palm_api_key)

    def get_supported_models(self) -> List[Model]:
        return PALM_MODELS

    def build_system_message(self) -> Message:
        return Message(
            role=Role.SYSTEM.value,
            content="You are Palm, a large language model trained by Google. Your job is to answer questions "
                    "accurately and provide detailed example."
        )

    def build_prompt(self, history: List[Optional[Message]]) -> Prompt:
        sys_message = self.build_system_message()
        all_messages = []

        for index, message in enumerate(history):
            if message is not None:
                # Some discord messages are split into chunks if content is too long, we have to concatenate them.
                if len(all_messages) > 0 and message.role == all_messages[-1].role:
                    if message.role == Role.USER.value:
                        all_messages[-1].content += f"\n{message.content}"
                    else:
                        all_messages[-1].content += message.content
                else:
                    all_messages.append(message)
            else:
                # Insert empty content for invalid message (e.g. blocked, error), as palm requires messages to be
                # alternating between authors.
                empty_msg = Message(
                    role=Role.ASSISTANT.value if all_messages[-1].role == Role.USER.value else Role.ASSISTANT.value,
                    content=' '
                )
                all_messages.append(empty_msg)

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
        return {
            "author": "0" if message.role == Role.USER.value else "1",
            "content": message.content
        }

    async def send_prompt(self, prompt: Prompt) -> CompletionData:
        rendered_prompt = self.render_prompt(prompt)
        logger.debug(dumps(rendered_prompt, indent=2, default=str))

        try:
            response = await palm.chat_async(
                context=prompt.header.content,
                messages=rendered_prompt,
                model=self.model.name
            )

            logger.debug(
                f"messages: ${response.messages}\ncandidates: {response.candidates}\nfilters: {response.filters}"
            )

            # CompletionResult.BLOCKED
            if len(response.filters) > 0:
                return CompletionData(
                    status=CompletionResult.BLOCKED,
                    reply_text=None,
                    status_text=f"{response.filters}",
                )

            # CompletionResult.OK
            return CompletionData(
                status=CompletionResult.OK,
                reply_text=response.last,
                status_text=None
            )
        except Exception as err:
            logger.exception(err)

            # CompletionResult.OTHER_ERROR
            return CompletionData(
                status=CompletionResult.OTHER_ERROR,
                reply_text=None,
                status_text=str(err)
            )

    async def count_token_usage(self, messages: List[Message]) -> int:
        token_count = await to_thread(self.__count_token_sync)
        return token_count

    def __count_token_sync(self, messages: List[Message]) -> int:
        response = palm.count_message_tokens(
            messages=[self.render_message(m) for m in messages],
            model=self.model.name
        )
        return response["token_count"]
