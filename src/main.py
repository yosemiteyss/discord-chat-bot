import asyncio
import logging
from typing import Optional

import discord
from discord import Message as DiscordMessage

from src.constant.discord import EMBED_FIELD_VALUE_LENGTH, ACTIVATE_THREAD_PREFIX, SECONDS_DELAY_RECEIVING_MSG, \
    MAX_THREAD_MESSAGES, EMBED_DESCRIPTION_LENGTH
from src.constant.env import CommonEnv
from src.message.discord_utils import logger, send_message_to_system_channel, allow_command, allow_message, \
    is_last_message_stale, discord_message_to_message
from src.message.process_response import process_response
from src.model.message import Message
from src.model.role import Role
from src.service.chat_service import ChatServiceType
from src.service.chat_service_factory import ChatServiceFactory

logging.basicConfig(
    format="[%(asctime)s] [%(filename)s:%(lineno)d] %(message)s",
    level=logging.DEBUG
)

intents = discord.Intents.default()
intents.message_content = True

# Load environment variables
common_env = CommonEnv.load()

# Create message client
client = discord.Client(intents=intents)
client.chat_service = ChatServiceFactory.get_service_cls(ChatServiceType(common_env.chat_service))
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    logger.info("We have logged in as %s. Invite URL: %s", client.user, common_env.bot_invite_url)

    await send_message_to_system_channel(
        client,
        message=f"<@{client.user.id}> is online, using `{client.chat_service.__class__.__name__} `🥳",
    )

    # Set current model name as game status
    if client.chat_service.model is not None:
        await client.change_presence(activity=discord.Game(name=client.chat_service.model.name))

    await tree.sync()


@tree.command(name="model", description="Switch chat completion model")
@discord.app_commands.checks.has_permissions(administrator=True)
@discord.app_commands.choices(models=[
    discord.app_commands.Choice(name=model.name, value=model.name) for model in
    client.chat_service.get_supported_models()
])
async def model_command(interaction: discord.Interaction, models: discord.app_commands.Choice[str]):
    if not allow_command(interaction, allow_server_ids=common_env.allow_server_ids):
        return

    # Update current model
    model_list = client.chat_service.get_supported_models()
    model = next((model for model in model_list if model.name == models.name), None)
    client.chat_service.set_current_model(model)

    # Set current model name as game status
    if client.chat_service.model is not None:
        await client.change_presence(activity=discord.Game(name=client.chat_service.model.name))

    # noinspection PyUnresolvedReferences
    await interaction.response.send_message(f"✅ Chat model switched to `{model.name}`")


@tree.command(name="chat", description="Create a new thread for conversation")
@discord.app_commands.checks.has_permissions(send_messages=True)
@discord.app_commands.checks.has_permissions(view_channel=True)
@discord.app_commands.checks.bot_has_permissions(send_messages=True)
@discord.app_commands.checks.bot_has_permissions(view_channel=True)
@discord.app_commands.checks.bot_has_permissions(manage_threads=True)
async def chat_command(interaction: discord.Interaction, message: str, attachment: Optional[discord.Attachment]):
    try:
        if not allow_command(interaction, allow_server_ids=common_env.allow_server_ids):
            return

        user = interaction.user
        logger.info(f"Chat command by {user} {message[:20]}")

        # Create embed message
        embed = discord.Embed(
            description=f"<@{user.id}> wants to chat! 🤖💬",
            color=discord.Color.green(),
        )
        embed.add_field(name=user.name, value=message[:EMBED_FIELD_VALUE_LENGTH])

        # Send embed message
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(embed=embed)
        response = await interaction.original_response()

        # Create a new thread for /chat
        thread = await response.create_thread(
            name=f"{ACTIVATE_THREAD_PREFIX} {user.name[:20]} - {message[:30]}",
            slowmode_delay=1,
            reason="chat_with_bot",
            auto_archive_duration=60,
        )

        # Check attachment is image
        image_url: Optional[str] = None
        if attachment is not None:
            if not attachment.content_type.startswith("image/"):
                raise Exception(f"Unsupported attachment type: {attachment.content_type}")

            if not client.chat_service.model.upload_image:
                raise Exception(f"{client.chat_service.model} does not support image upload")

            logger.debug(f"Uploaded attachment: {attachment.url}")
            image_url = attachment.url

        # Send chat request
        async with thread.typing():
            new_message = Message(role=Role.USER.value, content=message, image_url=image_url)
            response_data = await client.chat_service.chat(history=[new_message])
            await process_response(thread=thread, response_data=response_data)

    except Exception as err:
        logger.exception(err)
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(f"Failed to start chat {str(err)}", ephemeral=True)


# calls for each message
@client.event
async def on_message(message: DiscordMessage):
    try:
        if not await allow_message(client, message, allow_server_ids=common_env.allow_server_ids):
            return

        thread = message.channel

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

        # Send chat request
        async with thread.typing():
            response_data = await client.chat_service.chat(
                history=[
                    discord_message_to_message(message)
                    async for message in thread.history(limit=MAX_THREAD_MESSAGES, oldest_first=True)
                ],
            )

        # there is another message, and it's not from us, so ignore this response
        if is_last_message_stale(
                interaction_message=message,
                last_message=thread.last_message,
                bot_id=client.user.id,
        ):
            return

        # send response
        await process_response(thread=thread, response_data=response_data)
    except Exception as err:
        logger.exception(err)


@tree.command(name="count_token", description="Count the token usage of a message")
@discord.app_commands.checks.bot_has_permissions(send_messages=True)
async def count_token(interaction: discord.Interaction, message: str):
    try:
        if not allow_command(interaction, allow_server_ids=common_env.allow_server_ids):
            return

        # noinspection PyUnresolvedReferences
        await interaction.response.defer()

        tokens = await client.chat_service.count_token_usage(
            messages=[Message(role=Role.USER.value, content=message)],
        )

        embed = discord.Embed(
            title=f"🔍 Estimated tokens of message: {tokens}",
            description=message[:EMBED_DESCRIPTION_LENGTH],
            color=discord.Color.purple()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    except Exception as err:
        logger.exception(err)
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"Failed to count token {str(err)}",
                color=discord.Color.red()
            ),
            ephemeral=True,
        )


client.run(common_env.discord_bot_token)
