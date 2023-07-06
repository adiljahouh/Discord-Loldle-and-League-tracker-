from discord.ext import commands, tasks
from riot import riotAPI
import os
import requests
from dotenv import load_dotenv
from database import cacheDB
from typing import Optional
class leagueCommands(riotAPI, commands.Cog):
    def __init__(self, bot, redisdb) -> None:
        load_dotenv()
        self.bot = bot
        self.redisdb = redisdb
        self.RIOTTOKEN = os.getenv("RIOTTOKEN")
        print(self.RIOTTOKEN)
        super().__init__(self.RIOTTOKEN)

    @commands.Cog.listener()
    async def on_ready(self):
        print("test")
        
    @commands.command()
    async def register(self, ctx, *args):
        riot_name = "".join(args)
        print(riot_name)
        author_discord_tag = str(ctx.author)
        discord_userid = str(ctx.author.id)
        try:
            puuid = super().get_puuid(riot_name)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 400 and e.response.status_code <=500:
                message = "Bad request error, refresh the API key or re-register your user"
            else:
                message = "Internal Server Error"
            await ctx.send(message)
            return
        self.redisdb.store_user(discord_userid, riot_name, puuid, author_discord_tag)
        response = f"Registering Riot ID: {discord_userid}\nDiscord Tag: {author_discord_tag}\nriotID: {riot_name}\nPUUID: {puuid}"
        await ctx.send(response)


    @commands.command()
    async def unregister(self, ctx, riotid="undefined"):
        author_discord_tag = str(ctx.author)
        userid = str(ctx.author.id)
        self.redisdb.remove_user(userid)
        response = f"Removing user from DB\nRiot ID: {riotid}\nDiscord Tag: {author_discord_tag}\nUserId {userid}"
        await ctx.send(response)

    @commands.command()
    async def summary(self, ctx, *args):
        print("yes")
        print("length ", len(args))
        try:
            if len(args) != 0:
                user = "".join(args)
                message = super().get_kda_by_user(user)
            else:
                print("nothing passed")
                print(str(ctx.author.id))
                puuid = self.redisdb.get_user_field(str(ctx.author.id), "puuid")
                print(puuid.decode('utf-8'))
                message = super().get_kda_by_puuid(puuid.decode('utf-8'))
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 400 and e.response.status_code <=500:
                message = "Bad request error, refresh the API key or re-register your user"
            else:
                message = "Internal Server Error"
        finally:
            await ctx.send(message)
        
async def setup(bot):
    redisDB = cacheDB(os.getenv("REDISURL"))
    print("adding commands...")
    await bot.add_cog(leagueCommands(bot, redisDB))