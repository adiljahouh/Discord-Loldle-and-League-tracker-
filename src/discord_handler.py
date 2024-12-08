import discord
from databases.loldle import loldleDB
from discord.ext import tasks, commands


class discBot(commands.Bot):
    def __init__(self, token, channel_id, loldle_db: loldleDB) -> None:
        self.token = token
        self.CHANNEL_ID = channel_id
        intents = discord.Intents.all()
        self.loldle_DB = loldle_db
        # intents.messages = True
        super().__init__(command_prefix='.', intents=intents)  # initialize the bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("GO")
        await self.loldle_DB.populate_if_needed()
        await self.change_presence(activity=discord.Game(name="Type .help"))

    async def start_bot(self):
        await self.start(self.token)


async def add_cog(bot, files: list):
    await bot.load_extension(files)
