import discord
import datetime
import requests
from discord.ext import tasks, commands


class discBot(commands.Bot):
    def __init__(self, token, channel_id) -> None:
        self.token = token
        self.CHANNEL_ID = channel_id
        intents = discord.Intents.all()
        # intents.messages = True
        super().__init__(command_prefix='.', intents=intents)  # initialize the bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready")
        await self.change_presence(activity=discord.Game(name="Type .help"))

    async def start_bot(self):
        await self.start(self.token)


async def add_cog(bot, files: list):
    await bot.load_extension(files)
