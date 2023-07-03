    # @commands.command
    # async def add(ctx, riotid):
    #     author_discord_tag = str(ctx.author)
    #     response = f"Riot ID: {riotid}\nDiscord Tag: {author_discord_tag}"
    #     print("DING")
    #     await ctx.send(response)
from discord.ext import commands, tasks
from riot import riotAPI
class leagueCommands(commands.Cog, riotAPI):
    def __init__(self, bot) -> None:
        self.bot = bot
        pass
    @commands.Cog.listener()
    async def on_ready(self):
        print("test")
        
    @commands.command()
    async def add(self, ctx, riotid):
        author_discord_tag = str(ctx.author)
        response = f"Riot ID: {riotid}\nDiscord Tag: {author_discord_tag}"
        await ctx.send(response)

    @commands.command()
    async def summary(self, ctx, riotid):
        # super().
        pass
        
async def setup(bot):
    print("adding commands...")
    await bot.add_cog(leagueCommands(bot))