from discord_handler import discBot, add_cog
import asyncio
from config import Settings

import sys

async def main():
    settings = Settings()
    my_bot = discBot(token=settings.DISCORDTOKEN, channel_id=settings.CHANNELID)
    #my_cogs = ["commands.league", "commands.animals", "commands.points", "commands.discord_moderation"]
    my_cogs = ["commands.league", "commands.animals", "commands.points", "commands.discord_moderation", "commands.loop"]
    for cog in my_cogs:
        await add_cog(my_bot, cog)
    await my_bot.start_bot()


if __name__ == "__main__":
    """Run the bot"""
    asyncio.run(main())
