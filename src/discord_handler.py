import discord
import datetime
import requests
from discord.ext import tasks, commands

class discBot(commands.Bot):
    def __init__(self, token, hook, channel_id) -> None:
        self.token = token
        self.hook = hook
        self.CHANNEL_ID = channel_id
        intents = discord.Intents.all()
        # intents.messages = True
        super().__init__(command_prefix='.', intents=intents) # initialize the bot

    async def start_bot(self):
        @self.event
        async def on_ready():
            print("ready")
        await super().start(self.token)
        print("HAHAHAHA")

    async def send_webhook_message(self):
         print(self.hook, " = hook")
         payload = {"test": self.hook}
         requests.post(self.hook, json=payload)

async def add_cog(bot, files: list):
    await bot.load_extension(files)