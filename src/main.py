from discord_handler import discBot, add_cog
import asyncio
from config import Settings

import sys

async def main():
    settings = Settings()
    my_bot = discBot(token=settings.DISCORDTOKEN, channel_id=settings.CHANNELID)
    my_cogs = ["loop", "league_commands", "animal_commands", "point_commands"]
    for cog in my_cogs:
        await add_cog(my_bot, cog)
    await my_bot.start_bot()


if __name__ == "__main__":
    asyncio.run(main())
