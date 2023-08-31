import logging
from typing import Optional, List
import discord

from src.constant.discord import ACTIVATE_THREAD_PREFIX, MAX_THREAD_MESSAGES, INACTIVATE_THREAD_PREFIX, \
    MAX_CHARS_PER_REPLY_MSG
from discord import Message as DiscordMessage

from src.model.message import Message
from src.model.role import Role

logger = logging.getLogger(__name__)


def discord_message_to_message(message: DiscordMessage) -> Optional[Message]:
    role = Role.ASSISTANT if message.author.bot else Role.USER
    if (
            message.type == discord.MessageType.thread_starter_message
            and message.reference.cached_message
            and len(message.reference.cached_message.embeds) > 0
            and len(message.reference.cached_message.embeds[0].fields) > 0
    ):
        field = message.reference.cached_message.embeds[0].fields[0]
        if field.value:
            return Message(role=role.value, content=field.value)
    else:
        if message.content:
            return Message(role=role.value, content=message.content)

    return None


def split_into_shorter_messages(message: str) -> List[str]:
    return [
        message[i: i + MAX_CHARS_PER_REPLY_MSG]
        for i in range(0, len(message), MAX_CHARS_PER_REPLY_MSG)
    ]


def is_last_message_stale(
        interaction_message: DiscordMessage,
        last_message: Optional[DiscordMessage],
        bot_id: int
) -> bool:
    return (
            last_message
            and last_message.id != interaction_message.id
            and last_message.author
            and last_message.author.id != bot_id
    )


async def close_thread(thread: discord.Thread):
    await thread.edit(name=INACTIVATE_THREAD_PREFIX)
    await thread.send(
        embed=discord.Embed(
            description="**Thread closed** - Context limit reached, closing...",
            color=discord.Color.blue(),
        )
    )
    await thread.edit(archived=True, locked=True)


def allow_command(interaction: discord.Interaction, allow_server_ids: List[int]) -> bool:
    # only support creating thread in text channel
    if not isinstance(interaction.channel, discord.TextChannel):
        return False

    # block servers not in allow list
    if should_block(guild=interaction.guild, allow_server_ids=allow_server_ids):
        return False

    return True


def should_block(guild: Optional[discord.Guild], allow_server_ids: List[int]) -> bool:
    if guild is None:
        # dm's not supported
        logger.info("DM not supported")
        return True

    if guild.id and guild.id not in allow_server_ids:
        # not allowed in this server
        logger.info("Guild %s not allowed", guild)
        return True

    return False


async def allow_message(client: discord.Client, message: DiscordMessage, allow_server_ids: List[int]) -> bool:
    # block servers not in allow list
    if should_block(guild=message.guild, allow_server_ids=allow_server_ids):
        return False

    # ignore messages from the bot
    if message.author == client.user:
        return False

    # ignore messages not in a thread
    channel = message.channel
    if not isinstance(channel, discord.Thread):
        return False

    # ignore threads not created by the bot
    thread = channel
    if thread.owner_id != client.user.id:
        return False

    # ignore threads that are archived locked or title is not what we want
    if thread.archived or thread.locked or not thread.name.startswith(ACTIVATE_THREAD_PREFIX):
        # ignore this thread
        return False

    # too many messages, no longer going to reply
    if thread.message_count > MAX_THREAD_MESSAGES:
        await close_thread(thread=thread)
        return False

    return True


async def send_message_to_system_channel(
        client: discord.Client,
        message: Optional[str],
        embed: Optional[discord.Embed] = None
):
    for guild in client.guilds:
        channel = guild.system_channel
        if channel and channel.permissions_for(guild.me).send_messages:
            await channel.send(message, embed=embed)
