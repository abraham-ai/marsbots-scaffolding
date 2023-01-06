import re
from typing import Optional
import discord


def is_mentioned(message: discord.Message, user: Optional[discord.ClientUser]) -> bool:
    if not user:
        return False
    return user.id in [m.id for m in message.mentions]


def replace_bot_mention(
    message_text: str,
    only_first: bool = True,
    replacement_str: str = "",
) -> str:
    """
    Removes all mentions from a message.
    :param message: The message to remove mentions from.
    :return: The message with all mentions removed.
    """
    if only_first:
        return re.sub(r"<@\d+>", replacement_str, message_text, 1)
    else:
        return re.sub(r"<@\d+>", replacement_str, message_text)


def replace_mentions_with_usernames(
    message_content: str,
    mentions,
    prefix: str = "",
    suffix: str = "",
) -> str:
    """
    Replaces all mentions with their usernames.
    :param message_content: The message to replace mentions in.
    :return: The message with all mentions replaced with their usernames.
    """
    for mention in mentions:
        message_content = message_content.replace(
            f"<@{mention.id}>",
            f"{prefix}{mention.display_name}{suffix}",
        )
    return message_content


def remove_role_mentions(message_text: str) -> str:
    """
    Removes all role mentions from a message.
    :param message_text: The message to remove role mentions from.
    :return: The message with all role mentions removed.
    """
    return re.sub(r"<@&\d+>", "", message_text)
