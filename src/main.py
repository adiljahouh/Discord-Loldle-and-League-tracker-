import os
from discord_handler import discBot, add_cog
from dotenv import load_dotenv
import asyncio

async def main():
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    CHANNEL = int(os.getenv("CHANNEL_ID"))
    HOOK = os.getenv("WEBHOOK")
    REDISURL = os.getenv("REDISURL")
    my_bot = discBot(token=TOKEN, hook=HOOK, channel_id=CHANNEL)
    my_cogs = ["loop", "commands"]
    for cog in my_cogs:
        await add_cog(my_bot, cog)
    await my_bot.start_bot()

if __name__ == "__main__":
     asyncio.run(main())