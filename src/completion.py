from dataclasses import dataclass
from enum import Enum
from json import dumps
from typing import Optional, List

import discord
import openai

from src.base import Message, Prompt, Conversation, Role
from src.constants import BOT_INSTRUCTIONS, OPENAI_API_KEY
from src.discord_utils import split_into_shorter_messages, close_thread, logger
from src.moderation import moderate_message
from src.moderation import (
    send_moderation_flagged_message,
    send_moderation_blocked_message,
)

MODEL = "gpt-3.5-turbo-0613"
openai.api_key = OPENAI_API_KEY


class CompletionResult(Enum):
    OK = 0
    TOO_LONG = 1
    INVALID_REQUEST = 2
    OTHER_ERROR = 3
    MODERATION_FLAGGED = 4
    MODERATION_BLOCKED = 5


@dataclass
class CompletionData:
    status: CompletionResult
    reply_text: Optional[str]
    status_text: Optional[str]


async def generate_completion_response(
        messages: List[Message], user: str
) -> CompletionData:
    try:
        prompt = Prompt(
            header=Message(role=Role.SYSTEM.value, content=BOT_INSTRUCTIONS),
            convo=Conversation(messages)
        )
        rendered = prompt.render()
        logger.debug(dumps(rendered, indent=2, default=str))

        response = await openai.ChatCompletion.acreate(
            model=MODEL,
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
        if content:
            flagged_str, blocked_str = moderate_message(
                message=(str(rendered) + content)[-500:], user=user
            )
            # CompletionResult.MODERATION_BLOCKED
            if len(blocked_str) > 0:
                return CompletionData(
                    status=CompletionResult.MODERATION_BLOCKED,
                    reply_text=content,
                    status_text=f"from_response:{blocked_str}",
                )
            # CompletionResult.MODERATION_FLAGGED
            if len(flagged_str) > 0:
                return CompletionData(
                    status=CompletionResult.MODERATION_FLAGGED,
                    reply_text=content,
                    status_text=f"from_response:{flagged_str}",
                )
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


async def process_response(
        user: str, thread: discord.Thread, response_data: CompletionData
):
    status = response_data.status
    reply_text = response_data.reply_text
    status_text = response_data.status_text

    if status is CompletionResult.OK or status is CompletionResult.MODERATION_FLAGGED:
        sent_message = None
        if not reply_text:
            # Send empty response message
            sent_message = await thread.send(
                embed=discord.Embed(
                    description=f"**Invalid response** - empty response",
                    color=discord.Color.yellow(),
                )
            )
        else:
            # Send response
            shorter_response = split_into_shorter_messages(reply_text)
            for r in shorter_response:
                sent_message = await thread.send(r)
        if status is CompletionResult.MODERATION_FLAGGED:
            # Send flagged response
            await send_moderation_flagged_message(
                guild=thread.guild,
                user=user,
                flagged_str=status_text,
                message=reply_text,
                url=sent_message.jump_url if sent_message else "no url",
            )
            await thread.send(
                embed=discord.Embed(
                    description=f"⚠️ **This conversation has been flagged by moderation.**",
                    color=discord.Color.yellow(),
                )
            )
    elif status is CompletionResult.MODERATION_BLOCKED:
        # Send blocked response
        await send_moderation_blocked_message(
            guild=thread.guild,
            user=user,
            blocked_str=status_text,
            message=reply_text,
        )
        await thread.send(
            embed=discord.Embed(
                description=f"❌ **The response has been blocked by moderation.**",
                color=discord.Color.red(),
            )
        )
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
