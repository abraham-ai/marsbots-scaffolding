import argparse
import os
from pathlib import Path

import yaml

from marsbots.platforms.discord.bot import MarsBot, MarsbotMetadata


def parse_manifest(bot_dir) -> MarsbotMetadata:
    manifest_path = bot_dir / "manifest.yml"
    with open(manifest_path, "r") as f:
        manifest = yaml.safe_load(f)
    return MarsbotMetadata(**manifest)


def start(
    bot_id: str,
) -> None:
    bot_dir = Path(__file__).parent / bot_id
    metadata = parse_manifest(bot_dir)
    print("Launching bot...")

    bot = MarsBot(metadata)
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarsBot")
    parser.add_argument("bot_id", help="ID of bot to load from /bots directory")
    args = parser.parse_args()
    start(args.bot_id)
