from dataclasses import dataclass
from enum import Enum
from json import dumps
from typing import Optional, List

import discord
import openai

from src.base import Message, Model, Prompt, Conversation, Role
from src.constants import BOT_INSTRUCTIONS, OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_API_VERSION, OPENAI_API_TYPE, \
    AZURE_DEPLOYMENT_NAMES
from src.discord_utils import split_into_shorter_messages, close_thread, logger

openai.api_key = OPENAI_API_KEY
openai.api_base = OPENAI_API_BASE
openai.api_type = OPENAI_API_TYPE
openai.api_version = OPENAI_API_VERSION


class CompletionResult(Enum):
    OK = 0
    TOO_LONG = 1
    INVALID_REQUEST = 2
    OTHER_ERROR = 3


@dataclass
class CompletionData:
    status: CompletionResult
    reply_text: Optional[str]
    status_text: Optional[str]


async def generate_completion_response(messages: List[Message], model: Model) -> CompletionData:
    try:
        prompt = Prompt(
            header=Message(role=Role.SYSTEM.value, content=BOT_INSTRUCTIONS),
            convo=Conversation(messages)
        )
        rendered = prompt.render()
        logger.debug(dumps(rendered, indent=2, default=str))

        response = await openai.ChatCompletion.acreate(
            engine=AZURE_DEPLOYMENT_NAMES[model],
            model=model.value,
            messages=rendered,
        )

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
        content = response['choices'][0]['message']['content']
        # CompletionResult.OK
        return CompletionData(
            status=CompletionResult.OK, reply_text=content, status_text=None
        )
    except openai.error.InvalidRequestError as e:
        # CompletionResult.TOO_LONG
        if "This model's maximum context length" in e.user_message:
            return CompletionData(
                status=CompletionResult.TOO_LONG, reply_text=None, status_text=str(e)
            )
        # CompletionResult.INVALID_REQUEST
        else:
            logger.exception(e)
            return CompletionData(
                status=CompletionResult.INVALID_REQUEST,
                reply_text=None,
                status_text=str(e),
            )
    except Exception as e:
        # CompletionResult.OTHER_ERROR
        logger.exception(e)
        return CompletionData(
            status=CompletionResult.OTHER_ERROR, reply_text=None, status_text=str(e)
        )


async def process_response(thread: discord.Thread, response_data: CompletionData):
    status = response_data.status
    reply_text = response_data.reply_text
    status_text = response_data.status_text

    if status is CompletionResult.OK:
        if not reply_text:
            # Send empty response message
            await thread.send(
                embed=discord.Embed(
                    description='**Invalid response** - empty response',
                    color=discord.Color.yellow(),
                )
            )
        else:
            # Send response
            shorter_response = split_into_shorter_messages(reply_text)
            for response in shorter_response:
                await thread.send(response)
    elif status is CompletionResult.TOO_LONG:
        # Close thread for too long response
        await close_thread(thread)
    elif status is CompletionResult.INVALID_REQUEST:
        # Send invalid request response
        await thread.send(
            embed=discord.Embed(
                description=f"**Invalid request** - {status_text}",
                color=discord.Color.yellow(),
            )
        )
    else:
        # Send unknown error response
        await thread.send(
            embed=discord.Embed(
                description=f"**Error** - {status_text}",
                color=discord.Color.yellow(),
            )
        )
