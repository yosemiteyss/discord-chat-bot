import logging
from json import dumps
from typing import List, Any, Optional

import openai
from tiktoken import encoding_for_model, get_encoding

from src.constant.env import OpenAIEnv
from src.constant.model import OPENAI_MODELS
from src.service.chat_service import ChatService
from src.model.completion_data import CompletionData, CompletionResult
from src.model.message import Message
from src.model.model import Model
from src.model.prompt import Prompt
from src.model.role import Role

logger = logging.getLogger(__name__)


class OpenAIService(ChatService):
    def __init__(self):
        super().__init__()
        env = OpenAIEnv.load()
        openai.api_key = env.openai_api_key

    def get_supported_models(self) -> List[Model]:
        return OPENAI_MODELS

    def build_system_message(self) -> Message:
        return Message(
            role=Role.SYSTEM.value,
            content="You are ChatGPT, a large language model trained by OpenAI. Your job is to answer questions "
                    "accurately and provide detailed example."
        )

    def build_prompt(self, history: List[Optional[Message]]) -> Prompt:
        sys_message = self.build_system_message()
        all_messages = [x for x in history if x is not None]
        return Prompt(conversation=all_messages, header=sys_message)

    def render_prompt(self, prompt: Prompt) -> List[dict[str, str]]:
        messages = []

        if prompt.header is not None:
            messages.append(self.render_message(prompt.header))

        messages.extend([self.render_message(message) for message in prompt.conversation])

        return messages

    def render_message(self, message: Message) -> dict[str, str]:
        rendered = {
            "role": message.role,
            "name": message.name,
            "content": message.content
        }
        return {k: v for k, v in rendered.items() if v is not None}

    async def create_chat_completion(self, rendered: List[dict[str, str]]) -> dict[str, Any]:
        return await openai.ChatCompletion.acreate(
            model=self.model.name,
            messages=rendered
        )

    async def send_prompt(self, prompt: Prompt) -> CompletionData:
        rendered_prompt = self.render_prompt(prompt)
        logger.debug(dumps(rendered_prompt, indent=2, default=str))

        # Chat completion response:
        # {
        #     "id": "chatcmpl-123",
        #     "object": "chat.completion",
        #     "created": 1677652288,
        #     "choices": [{
        #         "index": 0,
        #         "message": {
        #             "role": "assistant",
        #             "content": "\n\nHello there, how may I assist you today?",
        #         },
        #         "finish_reason": "stop"
        #     }],
        #     "usage": {
        #         "prompt_tokens": 9,
        #         "completion_tokens": 12,
        #         "total_tokens": 21
        #     }
        # }
        try:
            response = await self.create_chat_completion(rendered_prompt)
            content = response['choices'][0]['message']['content']

            # CompletionResult.OK
            return CompletionData(
                status=CompletionResult.OK,
                reply_text=content,
                status_text=None
            )
        except openai.InvalidRequestError as err:
            # CompletionResult.TOO_LONG
            if "This model's maximum context length" in err.user_message:
                return CompletionData(
                    status=CompletionResult.TOO_LONG,
                    reply_text=None,
                    status_text=str(err)
                )

            # CompletionResult.INVALID_REQUEST
            logger.exception(err)
            return CompletionData(
                status=CompletionResult.INVALID_REQUEST,
                reply_text=None,
                status_text=str(err),
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
        """Returns the number of tokens used by a list of messages."""
        if self.model is None:
            raise ValueError("Model is not set.")

        try:
            encoding = encoding_for_model(self.model.name)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = get_encoding("cl100k_base")

        if self.model.name.startswith('gpt-3.5-turbo-'):
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif self.model.name.startswith('gpt-4-'):
            tokens_per_message = 3
            tokens_per_name = 1
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {self.model.name}. See https://github.com
                /openai/openai -python/blob/main/chatml.md for information on how messages are converted to tokens."""
            )

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in self.render_message(message).items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name

        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens
