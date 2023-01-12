import os
from typing import Optional
from bson import ObjectId
import discord
from discord.ext import commands
from marsbots.platforms.discord import (
    is_mentioned,
    remove_role_mentions,
    replace_bot_mention,
    replace_mentions_with_usernames,
)
from marsbots.capabilities.character import CharacterCapability


class CharacterCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        prompt = self.load_prompt()
        if prompt is None:
            raise Exception("No prompt found for this bot. Please add one.")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key is None:
            raise Exception(
                "No OpenAI API key found. Please set one in your .env file."
            )
        self.capability = CharacterCapability(
            name=self.bot.metadata.name,
            prompt=prompt,
            api_key=self.openai_api_key,
            cache_connection=os.getenv("REDIS_URI"),
        )

    def load_prompt(self) -> Optional[str]:
        db = self.bot.db
        personality = db.personalities.find_one({"_id": ObjectId(self.bot.metadata.id)})
        if personality:
            return personality["prompt"]

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        if (is_mentioned(message, self.bot.user)) and not message.author.bot:
            print("Handling reply")
            ctx = await self.bot.get_context(message)
            async with ctx.channel.typing():
                message_content = self.message_preprocessor(message)
                completion = self.capability.reply_to_message(
                    message_content, sender_name="M"
                )
                await message.reply(completion)
                print("Reply sent")

    def message_preprocessor(self, message: discord.Message) -> str:
        message_content = replace_bot_mention(message.content, only_first=True)
        message_content = replace_mentions_with_usernames(
            message_content,
            message.mentions,
        )
        message_content = remove_role_mentions(message_content)
        message_content = message_content.strip()
        return message_content


def setup(bot: commands.Bot) -> None:
    bot.add_cog(CharacterCog(bot))
