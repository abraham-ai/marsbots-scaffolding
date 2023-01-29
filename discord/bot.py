import argparse
from dataclasses import fields
import os
from bson import ObjectId

import discord
from discord.ext import commands
from marsbots.models import Command
from marsbots.platforms.discord.externals import init_llm
from marsbots.platforms.discord.models import MarsbotMetadata
from marsbots.platforms.discord.transformers import (
    transform_capability,
    transform_modifier,
    transform_trigger,
)
from marsbots.models import Character
from pymongo import MongoClient


UNLIKELY_PREFIX = ["438974983724798uyfsduhfksdhfjhksdbfhjgsdyfgsdygfusfd"]


class MarsBot(commands.Bot):
    def __init__(self, bot_id: str) -> None:
        self.bot_id = bot_id

        client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = client["marsbots"]

        self.character = self.get_character()

        intents = discord.Intents.default()
        self.set_intents(intents)

        self.llm = init_llm()

        self.capabilities = list(self.build_commands())

        super().__init__(
            command_prefix=UNLIKELY_PREFIX,
            intents=intents,
        )

    def set_intents(self, intents: discord.Intents) -> None:
        intents.message_content = True
        intents.messages = True
        if self.metadata.intents:
            if "presence" in self.metadata.intents:
                intents.presences = True
            if "members" in self.metadata.intents:
                intents.members = True

    def get_character(self):
        character_doc = self.db.characters.find_one({"_id": ObjectId(self.bot_id)})
        if not character_doc:
            raise ValueError(f"Character {self.bot_id} not found.")
        character_fields = {f.name: f for f in fields(Character)}
        filtered_character_doc = {
            k: v for k, v in character_doc.items() if k in character_fields
        }
        self.metadata = MarsbotMetadata(
            name=character_doc["name"],
        )
        return filtered_character_doc

    def build_commands(self):
        for command in self.character["commands"]:
            trigger = transform_trigger(command["trigger"])
            modifiers = [transform_modifier(check) for check in command["modifiers"]]
            capabilities = [
                transform_capability(capability)
                for capability in command["capabilities"]
            ]
            yield Command(
                trigger=trigger, modifiers=modifiers, capabilities=capabilities
            )

    async def on_ready(self) -> None:
        print(f"Running {self.metadata.name}...")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        for capability in self.capabilities:
            if capability.trigger(self, message):
                for modifier in capability.modifiers:
                    if not modifier(message):
                        await message.reply("This command is not available here.")
                        return
                for capability in capability.capabilities:
                    await capability.call(self, message)

        await self.process_commands(message)


def start(
    bot_id: str,
) -> None:
    print("Launching bot....")
    bot = MarsBot(bot_id)
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarsBot")
    parser.add_argument("bot_id", help="ID of bot to load from /bots directory")
    args = parser.parse_args()
    start(args.bot_id)
