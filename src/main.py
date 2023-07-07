import asyncio
import logging

import discord
from discord import Message as DiscordMessage

from src.base import Message, Role, Model
from src.completion import generate_completion_response, process_response
from src.constants import (
    BOT_INVITE_URL,
    DISCORD_BOT_TOKEN,
    ACTIVATE_THREAD_PREFIX,
    MAX_THREAD_MESSAGES,
    SECONDS_DELAY_RECEIVING_MSG, EMBED_FIELD_VALUE_LENGTH, EMBED_DESCRIPTION_LENGTH
)
from src.discord_utils import (
    logger,
    is_last_message_stale,
    discord_message_to_message, allow_command, allow_message, send_message_to_system_channel,
)
from src.moderation import (
    moderate_message,
    send_moderation_blocked_message,
    send_moderation_flagged_message,
    ModerationOption,
)
from src.usage import get_usage_embed_message, count_token_usage

logging.basicConfig(
    format="[%(asctime)s] [%(filename)s:%(lineno)d] %(message)s", level=logging.DEBUG
)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Control if moderation is required for each message.
client.moderation_option = ModerationOption.OFF
client.model = Model.GPT35_TURBO


@client.event
async def on_ready():
    logger.info(f"We have logged in as {client.user}. Invite URL: {BOT_INVITE_URL}")
    await send_message_to_system_channel(client, message=f"<@{client.user.id}> is online. 🥳", embed=None)
    await tree.sync()


# /model
@tree.command(name="model", description="Switch chat completion model")
@discord.app_commands.checks.has_permissions(administrator=True)
async def model_command(interaction: discord.Interaction, model: Model):
    if not allow_command(interaction):
        return

    client.model = model
    await interaction.response.send_message(f"✅ Chat completion model switched to `{model}`")


# /moderation
@tree.command(name="moderation", description="Toggle on or off moderation")
@discord.app_commands.checks.has_permissions(administrator=True)
async def moderation_command(interaction: discord.Interaction, option: ModerationOption):
    if not allow_command(interaction):
        return

    # TODO: save option per server
    client.moderation_option = option

    match option:
        case ModerationOption.ON:
            await interaction.response.send_message("✅ Moderation is enabled")
        case ModerationOption.OFF:
            await interaction.response.send_message("❌ Moderation is disabled")


# /usage
@tree.command(name="usage", description="Check usage")
@discord.app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.checks.bot_has_permissions(send_messages=True)
async def usage_command(interaction: discord.Interaction):
    try:
        if not allow_command(interaction):
            return

        await interaction.response.defer()
        embed = await get_usage_embed_message()
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.exception(e)
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"Failed to check usage {str(e)}",
                color=discord.Color.red()
            ),
            ephemeral=True,
        )


# /chat message:
@tree.command(name="chat", description="Create a new thread for conversation")
@discord.app_commands.checks.has_permissions(send_messages=True)
@discord.app_commands.checks.has_permissions(view_channel=True)
@discord.app_commands.checks.bot_has_permissions(send_messages=True)
@discord.app_commands.checks.bot_has_permissions(view_channel=True)
@discord.app_commands.checks.bot_has_permissions(manage_threads=True)
async def chat_command(interaction: discord.Interaction, message: str):
    try:
        if not allow_command(interaction):
            return

        user = interaction.user
        logger.info(f"Chat command by {user} {message[:20]}")

        try:
            # Create embed message
            embed = discord.Embed(
                description=f"<@{user.id}> wants to chat! 🤖💬",
                color=discord.Color.green(),
            )
            embed.add_field(name=user.name, value=message[:EMBED_FIELD_VALUE_LENGTH])

            flagged_str = None

            # moderate the message
            if client.moderation_option == ModerationOption.ON:
                flagged_str, blocked_str = moderate_message(message=message, user=user.name)
                # Send blocked message
                await send_moderation_blocked_message(
                    guild=interaction.guild,
                    user=user.name,
                    blocked_str=blocked_str,
                    message=message,
                )

                # Return if message was blocked
                if len(blocked_str) > 0:
                    await interaction.response.send_message(
                        f"Your prompt has been blocked by moderation.\n{message}",
                        ephemeral=True,
                    )
                    return

                # message was flagged
                if len(flagged_str) > 0:
                    embed.color = discord.Color.yellow()
                    embed.title = "⚠️ This prompt was flagged by moderation."

            # Send embed message
            await interaction.response.send_message(embed=embed)
            response = await interaction.original_response()

            # Send flagged message
            if client.moderation_option == ModerationOption.ON:
                await send_moderation_flagged_message(
                    guild=interaction.guild,
                    user=user.name,
                    flagged_str=flagged_str,
                    message=message,
                    url=response.jump_url,
                )
        except Exception as e:
            logger.exception(e)
            await interaction.response.send_message(
                f"Failed to start chat {str(e)}", ephemeral=True
            )
            return

        # create a new thread for /chat
        thread = await response.create_thread(
            name=f"{ACTIVATE_THREAD_PREFIX} {user.name[:20]} - {message[:30]}",
            slowmode_delay=1,
            reason="gpt-bot",
            auto_archive_duration=60,
        )

        async with thread.typing():
            # fetch completion
            messages = [Message(role=Role.USER.value, content=message)]
            response_data = await generate_completion_response(
                messages=messages, user=user.name, model=client.model
            )
            # send the result
            await process_response(
                user=user.name, thread=thread, response_data=response_data
            )
    except Exception as e:
        logger.exception(e)
        await interaction.response.send_message(
            f"Failed to start chat {str(e)}", ephemeral=True
        )


@tree.command(name="count_token", description="Count the token usage of a message")
@discord.app_commands.checks.bot_has_permissions(send_messages=True)
async def count_token(interaction: discord.Interaction, message: str):
    try:
        if not allow_command(interaction):
            return

        await interaction.response.defer()
        tokens = count_token_usage(
            messages=[Message(role=Role.USER.value, content=message)],
            model=client.model
        )
        embed = discord.Embed(
            title=f"🔍 Estimated tokens of message: {tokens}",
            description=message[:EMBED_DESCRIPTION_LENGTH],
            color=discord.Color.purple()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as e:
        logger.exception(e)
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"Failed to count token {str(e)}",
                color=discord.Color.red()
            ),
            ephemeral=True,
        )


# calls for each message
@client.event
async def on_message(message: DiscordMessage):
    try:
        if not await allow_message(client, message):
            return

        thread = message.channel

        # moderate the message
        if client.moderation_option == ModerationOption.ON:
            flagged_str, blocked_str = moderate_message(
                message=message.content, user=message.author.name
            )
            await send_moderation_blocked_message(
                guild=message.guild,
                user=message.author.name,
                blocked_str=blocked_str,
                message=message.content,
            )

            # message was blocked
            if len(blocked_str) > 0:
                # noinspection PyBroadException
                try:
                    await message.delete()
                    await thread.send(
                        embed=discord.Embed(
                            description=f"❌ **{message.author}'s message has been deleted by moderation.**",
                            color=discord.Color.red(),
                        )
                    )
                    return
                except Exception:
                    await thread.send(
                        embed=discord.Embed(
                            description=f"❌ **{message.author}'s message has been blocked by moderation but could not "
                                        f"be deleted. Missing Manage Messages permission in this Channel.**",
                            color=discord.Color.red(),
                        )
                    )
                    return

            await send_moderation_flagged_message(
                guild=message.guild,
                user=message.author.name,
                flagged_str=flagged_str,
                message=message.content,
                url=message.jump_url,
            )

            # message was flagged
            if len(flagged_str) > 0:
                await thread.send(
                    embed=discord.Embed(
                        description=f"⚠️ **{message.author}'s message has been flagged by moderation.**",
                        color=discord.Color.yellow(),
                    )
                )

        # wait a bit in case user has more messages
        if SECONDS_DELAY_RECEIVING_MSG > 0:
            await asyncio.sleep(SECONDS_DELAY_RECEIVING_MSG)
            if is_last_message_stale(
                    interaction_message=message,
                    last_message=thread.last_message,
                    bot_id=client.user.id,
            ):
                # there is another message, so ignore this one
                return

        logger.info(
            f"Thread message to process - {message.author}: {message.content[:50]} - {thread.name} {thread.jump_url}"
        )

        channel_messages = [
            discord_message_to_message(message)
            async for message in thread.history(limit=MAX_THREAD_MESSAGES)
        ]
        channel_messages = [x for x in channel_messages if x is not None]
        channel_messages.reverse()

        # generate the response
        async with thread.typing():
            response_data = await generate_completion_response(
                messages=channel_messages, user=message.author.name, model=client.model
            )

        # there is another message, and it's not from us, so ignore this response
        if is_last_message_stale(
                interaction_message=message,
                last_message=thread.last_message,
                bot_id=client.user.id,
        ):
            return

        # send response
        await process_response(
            user=message.author.name, thread=thread, response_data=response_data
        )
    except Exception as e:
        logger.exception(e)


client.run(DISCORD_BOT_TOKEN)
