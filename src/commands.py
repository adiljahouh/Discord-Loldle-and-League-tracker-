from discord.ext import commands, tasks
from riot import riotAPI
import os
import requests
from config import Settings
from database import cacheDB
from typing import Optional
import discord
class leagueCommands(riotAPI, commands.Cog):
    def __init__(self, bot, redisdb, riot_api) -> None:
        self.bot: commands.bot.Bot = bot
        self.redisdb: cacheDB= redisdb
        self.riot_api: riotAPI = riot_api

    @commands.Cog.listener()
    async def on_ready(self):
        pass
        
    @commands.command()
    async def register(self, ctx, *args):
        """ Register a user by calling .register <your_league_name>"""
        riot_name = "".join(args)
        if len(riot_name) ==0:
            await ctx.send("Specify a riot username")
            return
        author_discord_tag = str(ctx.author)
        discord_userid = str(ctx.author.id)
        try:
            puuid = self.riot_api.get_puuid(riot_name)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 400 and e.response.status_code <=500:
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
        try:
            response = requests.get("https://dog.ceo/api/breeds/image/random")
            response.raise_for_status()
            if response.content['status'] == 'success':
                ctx.send(response.content[''])
            else:
                ctx.send("Internal API error")
        except requests.exceptions.HTTPError as e:
            await ctx.send("HTTP error, no dogs for you")



    @commands.command()
    async def summary(self, ctx, *args):
        """ Summary of a user (or your registered user if nothing is passed)
          by calling .summary <league_name> or just .summary"""
        try:
            if len(args) != 0:
                user = "".join(args)
                message = self.riot_api.get_kda_by_user(user)
            else:
                puuid = self.redisdb.get_user_field(str(ctx.author.id), "puuid")
                message = self.riot_api.get_kda_by_puuid(puuid.decode('utf-8'))
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 400 and e.response.status_code <=500:
                message = "Bad request error, refresh the API key or re-register your user"
            else:
                message = "Internal Server Error"
        finally:
            embed = discord.Embed(title="📓Summary of last 5 games📓\n\n", 
            description=f"{message}",
            color=0xFF0000)
            await ctx.send(embed=embed)
        
async def setup(bot):
    settings = Settings()
    redisDB = cacheDB(settings.REDISURL)
    riot_api = riotAPI(settings.RIOTTOKEN)
    print("adding commands...")
    await bot.add_cog(leagueCommands(bot, redisDB, riot_api))