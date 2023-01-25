import argparse
from dataclasses import fields
import os
from bson import ObjectId

import discord
from discord.ext import commands
from marsbots.models import Capability
from marsbots.platforms.discord.externals import init_llm
from marsbots.platforms.discord.models import MarsbotMetadata
from marsbots.platforms.discord.transformers import (
    transform_behavior,
    transform_check,
    transform_trigger,
)
from marsbots.models import Personality
from pymongo import MongoClient


UNLIKELY_PREFIX = ["438974983724798uyfsduhfksdhfjhksdbfhjgsdyfgsdygfusfd"]


class MarsBot(commands.Bot):
    def __init__(self, bot_id: str) -> None:
        self.bot_id = bot_id

        client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = client["marsbots"]

        self.personality = self.get_personality()

        intents = discord.Intents.default()
        self.set_intents(intents)

        self.llm = init_llm()

        self.capabilities = list(self.build_capabilities())

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

    def get_personality(self):
        personality_doc = self.db.personalities.find_one({"_id": ObjectId(self.bot_id)})
        if not personality_doc:
            raise ValueError(f"Personality {self.bot_id} not found.")
        personality_fields = {f.name: f for f in fields(Personality)}
        filtered_personality_doc = {
            k: v for k, v in personality_doc.items() if k in personality_fields
        }
        self.metadata = MarsbotMetadata(
            name=personality_doc["name"],
        )
        return filtered_personality_doc

    def build_capabilities(self):
        for capability in self.personality["capabilities"]:
            trigger = transform_trigger(capability["trigger"])
            checks = [transform_check(check) for check in capability["checks"]]
            behaviors = [
                transform_behavior(behavior) for behavior in capability["behaviors"]
            ]
            yield Capability(trigger=trigger, checks=checks, behaviors=behaviors)

    async def on_ready(self) -> None:
        print(f"Running {self.metadata.name}...")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        for capability in self.capabilities:
            if capability.trigger(self, message):
                for check in capability.checks:
                    if not check(message):
                        await message.reply("This command is not available here.")
                        return
                for behavior in capability.behaviors:
                    await behavior.call(self, message)

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
