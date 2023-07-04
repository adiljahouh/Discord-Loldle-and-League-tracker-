    # @commands.command
    # async def add(ctx, riotid):
    #     author_discord_tag = str(ctx.author)
    #     response = f"Riot ID: {riotid}\nDiscord Tag: {author_discord_tag}"
    #     print("DING")
    #     await ctx.send(response)
from discord.ext import commands, tasks
from riot import riotAPI
import os
from dotenv import load_dotenv
class leagueCommands(riotAPI, commands.Cog):
    def __init__(self, bot) -> None:
        load_dotenv()
        self.bot = bot
        self.RIOTTOKEN = os.getenv("RIOTTOKEN")
        super().__init__(self.RIOTTOKEN)

    @commands.Cog.listener()
    async def on_ready(self):
        print("test")
        
    @commands.command()
    async def add(self, ctx, riotid):
        author_discord_tag = str(ctx.author)
        response = f"Riot ID: {riotid}\nDiscord Tag: {author_discord_tag}"
        await ctx.send(response)

    @commands.command()
    async def summary(self, ctx, user):
        message = super().get_kda_by_user(user)
        await ctx.send(message)
        
async def setup(bot):
    print("adding commands...")
    await bot.add_cog(leagueCommands(bot))