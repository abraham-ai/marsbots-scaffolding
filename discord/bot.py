import argparse
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import discord
from discord.ext import commands
from pymongo import MongoClient
import yaml


@dataclass
class MarsbotMetadata:
    id: str
    name: str
    capabilities: list[str]

    intents: Optional[list[str]] = None
    command_prefix: Optional[str] = None


UNLIKELY_PREFIX = ["438974983724798uyfsduhfksdhfjhksdbfhjgsdyfgsdygfusd"]


def parse_manifest(bot_dir) -> MarsbotMetadata:
    manifest_path = bot_dir / "manifest.yml"
    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)
        print(manifest)
    return MarsbotMetadata(**manifest)


class MarsBot(commands.Bot):
    def __init__(self, metadata: MarsbotMetadata) -> None:
        self.metadata = metadata

        client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = client["marsbots"]

        intents = discord.Intents.default()
        self.set_intents(intents)
        commands.Bot.__init__(
            self,
            command_prefix=self.metadata.command_prefix or UNLIKELY_PREFIX,
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

    async def on_ready(self) -> None:
        print(f"Running {self.metadata.name}...")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)


def start(
    bot_id: str,
) -> None:

    bot_dir = Path(__file__).parent / bot_id
    metadata = parse_manifest(bot_dir)
    print("Launching bot...")

    bot = MarsBot(metadata)
    cog_paths = [f"{bot_id}.cogs.{cog.stem}" for cog in bot_dir.glob("cogs/*.py")]
    for path in cog_paths:
        bot.load_extension(path)
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarsBot")
    parser.add_argument("bot_id", help="ID of bot to load from /bots directory")
    args = parser.parse_args()
    start(args.bot_id)
