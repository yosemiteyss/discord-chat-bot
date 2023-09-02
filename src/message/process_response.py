import discord

from src.message.discord_utils import split_into_shorter_messages, close_thread
from src.model.completion_data import CompletionData, CompletionResult


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
    elif status is CompletionResult.BLOCKED:
        # Send blocked request response
        await thread.send(
            embed=discord.Embed(
                description=f"**Message blocked** - {status_text}",
                color=discord.Color.pink(),
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
