from discord.ext import commands, tasks
from riot import riotAPI
import aiohttp
import requests
from config import Settings
from database import cacheDB
from typing import Optional
import discord
import json
import asyncio
from redis.exceptions import ConnectionError
class leagueCommands(riotAPI, commands.Cog):
    def __init__(self, bot, redisdb, riot_api) -> None:
        self.bot: commands.bot.Bot = bot
        self.redisdb: cacheDB= redisdb
        self.riot_api: riotAPI = riot_api

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def leaderboard(self, ctx):  
        """
            Keeps track of top 5 in each role of the leaderboard
        """
        async with ctx.typing():
            try:
                discord_ids: list[bytes] = self.redisdb.get_all_users()
            except ConnectionError as e:
                await ctx.send("Could not connect to database.")
                return
            leaderboard_text = ''
            if len(discord_ids) > 0:
                discord_ids = [id.decode('utf-8') for id in discord_ids]
            else:
                await ctx.send("No users are registered.")
            tasks= []
            delay = 0.5
            for discord_id in discord_ids:
                puuid = self.redisdb.get_user_field(discord_id, "puuid")
                tasks.append(self.riot_api.get_highest_damage_taken_by_puuid(puuid=puuid.decode('utf-8'), count=10, sleep_time=delay, discord_id = discord_id))
                delay += 1
            try:
                result = await asyncio.gather(*tasks)
            except aiohttp.ClientResponseError as e:
                print(e)
                await ctx.send(e.message + ', please wait a minute.')
                return
            top_5 = sorted(result, key=lambda x: x['taken'], reverse=True)[:5]
            for index, top_g in enumerate(top_5):
                leaderboard_text += f'\n{index+1}. <@{top_g["disc_id"]}> | {top_g["taken"]} on **{top_g["champion"]}**'
            description = f"Type .register to be able to participate"
            embed = discord.Embed(title="💪🏽TOPPEST G's💪🏽\n\n", 
                            description=f"{description}",
                            color=0xFF0000)
            embed.add_field(name="Top Damage Taken Past 5 Games", value = leaderboard_text)
            await ctx.send(embed=embed)

    @leaderboard.error
    async def on_command_error(ctx, error):
        print("triggered")
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'This command is actually on cooldown, you can use it in {round(error.retry_after, 2)} seconds.')

    @commands.command()
    async def register(self, ctx, *args):
        """ Register a user by calling .register <your_league_name>"""
        async with ctx.typing():
            riot_name = "".join(args)
            if len(riot_name) ==0:
                await ctx.send("Specify a riot username")
                return
            author_discord_tag = str(ctx.author)
            discord_userid = str(ctx.author.id)
            try:
                puuid = await self.riot_api.get_puuid(riot_name)
            except aiohttp.ClientResponseError as e:
                if e.status >= 400 and e.status <=500:
                    message = "Bad request error, refresh the API key or re-register your user"
                else:
                    message = "Internal Server Error"
                await ctx.send(message)
                return
            self.redisdb.store_user(discord_userid, riot_name, puuid, author_discord_tag)
            response = f"**Riot ID**: {discord_userid}\
            \n**Discord Tag:** {author_discord_tag}\n**Riot User:** {riot_name}"
            embed = discord.Embed(title="📠Registering User📠\n\n", 
                            description=f"{response}",
                            color=0xFF0000)
            await ctx.send(embed=embed)


    @commands.command()
    async def deregister(self, ctx, riotid="undefined"):
        
        """ deregister a user by calling .deregister <your_league_name>"""
        async with ctx.typing():
            author_discord_tag = str(ctx.author)
            userid = str(ctx.author.id)
            riot_name = self.redisdb.remove_user(userid)
            if riot_name != None:
                response = f"**Riot ID**: {userid}\
                \n**Discord Tag:** {author_discord_tag}\n**Riot User:** {riot_name.decode('utf-8')}"
            else:
                response = "No user found for discord ID"
            embed = discord.Embed(title="📠Deregistering User📠\n\n", 
                    description=f"{response}",
                    color=0xFF0000)
            await ctx.send(embed=embed)
    
    @commands.command()
    async def dog(self, ctx):
        """
            Returns a dog pic
        """
        async with ctx.typing():
            try:
                response = requests.get("https://dog.ceo/api/breeds/image/random")
                content = json.loads(response.content.decode("utf-8"))

                response.raise_for_status()
                if content['status'] == 'success':
                    await ctx.send(content['message'])
                else:
                    await ctx.send("Internal API error")
            except requests.exceptions.HTTPError as e:
                await ctx.send("HTTP error, no dogs for you")



    @commands.command()
    async def summary(self, ctx, *args):
        
        """ Summary of a user (or your registered user if nothing is passed)
          by calling .summary <league_name> or just .summary"""
        async with ctx.typing():
            try:
                count = 10
                if len(args) != 0:
                    user = "".join(args)
                    message = await self.riot_api.get_kda_by_user(user, count)
                else:
                    puuid = self.redisdb.get_user_field(str(ctx.author.id), "puuid")
                    message = await self.riot_api.get_kda_by_puuid(puuid.decode('utf-8'), count)
            except aiohttp.ClientResponseError as e:
                if e.status >= 400 and e.status <=500:
                    message = "Bad request error, refresh the API key or re-register your user"
                else:
                    message = "Internal Server Error"
            finally:
                embed = discord.Embed(title=f"📓Summary of last {count} games📓\n\n", 
                description=f"{message}",
                color=0xFF0000)
                await ctx.send(embed=embed)
        
async def setup(bot):
    settings = Settings()
    redisDB = cacheDB(settings.REDISURL)
    riot_api = riotAPI(settings.RIOTTOKEN)
    print("adding commands...")
    await bot.add_cog(leagueCommands(bot, redisDB, riot_api))