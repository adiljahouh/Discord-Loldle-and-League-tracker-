import discord
from discord.ext import commands


class discBot(commands.Bot):
    def __init__(self, token) -> None:
        self.token = token
        intents = discord.Intents.all()
        # intents.messages = True
        super().__init__(command_prefix='.', intents=intents)  # initialize the bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name="Type .help"))

    async def start_bot(self):
        await self.start(self.token)


async def add_cog(bot, files: list):
    await bot.load_extension(files)
