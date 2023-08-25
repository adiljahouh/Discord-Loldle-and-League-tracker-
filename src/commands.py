from discord.ext import commands, tasks
from riot import riotAPI
import aiohttp
import requests
from config import Settings
from database import cacheDB
from typing import Optional
import discord
import os
import random
import json
import asyncio
from redis.exceptions import ConnectionError
import uuid
import functools
import datetime
class leagueCommands(riotAPI, commands.Cog):
    def __init__(self, bot, redisdb, riot_api, jail_role_id, player_role_id, g_role) -> None:
        self.bot: commands.bot.Bot = bot
        self.redisdb: cacheDB= redisdb
        self.riot_api: riotAPI = riot_api
        self.jail_role = jail_role_id
        self.player_role = player_role_id
        self.g_role = g_role

    @commands.Cog.listener()
    async def on_ready(self):
        pass
  
    #FIXME: can now change this to role check, not registery
    def check_registery(func):
        @functools.wraps(func)
        async def inner(self, ctx, *args, **kwargs):
            try:
                discord_ids: list[bytes] = self.redisdb.get_all_users()
                ids = [id.decode('utf-8') for id in discord_ids]
                for id in ids:
                    if str(id) == str(ctx.author.id):
                        return await func(self, ctx, *args, **kwargs)
                await ctx.send("You need to register using .register <league_name> to use this bot.")   
            except ConnectionError as e:
                print("ooooo")
                await ctx.send("Could not connect to database to verify users.")
                return
        return inner
    
    def mod_check(func):
        @functools.wraps(func)
        async def inner(self, ctx, *args, **kwargs):
            try:
                for role in ctx.author.roles:
                    if role.id == self.player_role:
                        print("Moderator validated")
                        return await func(self, ctx, *args, **kwargs)
                required_role = ctx.guild.get_role(self.player_role)
                await ctx.send(f"You need the {required_role.mention} role to use this command.")   
            except Exception as e:
                await ctx.send(f"Error occured during role check, Error: {e}")
                return
        return inner
    @commands.command()
    @check_registery
    async def duck(self, ctx):
        """
            Returns a duck pic or gif
        """
        #TODO: add retry logic
        async with ctx.typing():
            if random.randint(0, 100) == 1:
                img = random.choice(os.listdir('../assets/menno_dogs'))
                await ctx.send("@here A VERY GOOD BOY APPEARS", file=discord.File(f'../assets/menno_dogs/{img}'))
            else:
                try:
                    response = requests.get("https://random-d.uk/api/v2/random")
                    content = json.loads(response.content.decode("utf-8"))
                    response.raise_for_status()
                    if content['url']:
                        await ctx.send(content['url'])
                    else:
                        await ctx.send("Internal API error")
                except requests.exceptions.HTTPError as e:
                    await ctx.send("HTTP error, no ducks for you")


    # @leaderboard.error
    # async def on_command_error(self, ctx, error):
    #     if isinstance(error, commands.CommandOnCooldown):
    #         await ctx.send(f'This command is actually on cooldown, you can use it in {round(error.retry_after, 2)} seconds.')  

    @commands.command()
    async def register(self, ctx, *args):
        """ Register a user by calling .register <your_league_name>"""
        async with ctx.typing():
            print("register")
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
            \n**Discord Tag:** {author_discord_tag}\n**Riot User:** {riot_name}\n**Strikes:** 0\n**Points:** 500"
            try:
                g_role = ctx.guild.get_role(self.g_role)
                await ctx.author.add_roles(g_role)
            except Exception as e:
                await ctx.send(e)
                return
            embed = discord.Embed(title="📠Registering User📠\n\n", 
                            description=f"{response}",
                            color=0xFF0000)
            await ctx.send(embed=embed)
    
    @commands.command()
    @check_registery
    @mod_check
    async def count(self, ctx):
        """
            Returns amount of users registered
        """
        async with ctx.typing():
            discord_ids: list[bytes] = self.redisdb.get_all_users()
            response =''
            for index, discord_id in enumerate(discord_ids):
                id = discord_id.decode('utf-8')
                response += f'\n{index+1}. <@{id}>'
            embed = discord.Embed(title="📠Users Registered📠\n\n", 
                    description=f"{response}",
                    color=0xFF0000)
            await ctx.send(embed=embed)
    
    @commands.command()
    @mod_check
    async def deregister(self, ctx, riotid="undefined"):
        
        """ deregister a user by calling .deregister <your_league_name>"""
        async with ctx.typing():
            author_discord_tag = str(ctx.author)
            userid = str(ctx.author.id)
            userinfo: dict = self.redisdb.remove_and_return_all(userid)
            if userinfo != None:
                response = f"**Riot ID**: {userid}\
                \n**Discord Tag:** {author_discord_tag}\n**Riot User:** {userinfo[b'riot_user'].decode('utf-8')}\n**Strikes:** {userinfo[b'strikes'].decode('utf-8')}"
            else:
                response = "No user found for discord ID"
            embed = discord.Embed(title="📠Deregistering User📠\n\n", 
                    description=f"{response}",
                    color=0xFF0000)
            await ctx.send(embed=embed)
    
    @commands.command()
    @check_registery
    async def dog(self, ctx):
        """
            Returns a dog pic
        """
        #TODO: add retry logic
        async with ctx.typing():
            if random.randint(0, 100) == 1:
                img = random.choice(os.listdir('../assets/menno_dogs'))
                await ctx.send("@here A VERY GOOD BOY APPEARS", file=discord.File(f'../assets/menno_dogs/{img}'))
            else:
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
    @check_registery
    async def cat(self, ctx):
        """
            Returns a cat pic
        """
        #TODO: add retry logic
        async with ctx.typing():
            if random.randint(0, 100) == 1:
                img = random.choice(os.listdir('../assets/menno_dogs'))
                await ctx.send("@here A VERY GOOD BOY APPEARS", file=discord.File(f'../assets/menno_dogs/{img}'))
            else:
                try:
                    response = requests.get("https://api.thecatapi.com/v1/images/search")
                    content = json.loads(response.content.decode("utf-8"))
                    response.raise_for_status()
                    if content[0]['url']:
                        await ctx.send(content[0]['url'])
                    else:
                        await ctx.send("Internal API error")
                except requests.exceptions.HTTPError as e:
                    await ctx.send("HTTP error, no cats for you")

    @commands.command()
    @check_registery
    async def daily(self, ctx):
        async with ctx.typing():
            today = datetime.datetime.now().date()
            userid = str(ctx.author.id)
            last_claim =  self.redisdb.get_user_field(discord_id=userid, field="last_claim")
            if last_claim.decode('utf-8') is None or last_claim.decode('utf-8') != str(today.strftime('%Y-%m-%d')):
                    status =  "You claim some points"
                    self.redisdb.set_user_field(userid, "last_claim", today.strftime('%Y-%m-%d'))
                    self.redisdb.increment_field(userid, "points", 500)
            else:
                status = "You already claimed your points for today"
            points_bytes = self.redisdb.get_user_field(userid, "points")
            points = points_bytes.decode('utf-8')
            message = f'Total points: {points}'
            embed = discord.Embed(title=f"{status}\n\n", 
                description=f"{message}",
                color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.command()
    @check_registery
    async def roll(self, ctx, number):
        async with ctx.typing():
            userid = str(ctx.author.id)
            points_bytes = self.redisdb.get_user_field(userid, "points")
            points = points_bytes.decode('utf-8')
            if int(number) > int(points):
                await ctx.send(f"You do not have enough points for this, total points: {points}")
                return
            roll = random.choice(['Heads', 'Tails'])
            print(roll)
            print(points)
            print(int(number))
            if roll != 'Heads':
                print("yes")
                try:
                    self.redisdb.decrement_field(userid, "points", number)
                except Exception as e:
                    print(e)
                print("test")
                new_points = self.redisdb.get_user_field(userid, "points")
                print(new_points)
                status = "LOLOLOLOLO-LOSER"
            else:
                self.redisdb.increment_field(userid, "points", number)
                new_points = self.redisdb.get_user_field(userid, "points")
                status = "You won!"
            embed = discord.Embed(title=f"{status}\n\n", 
                description=f"Original points: {points}\nNew points: {new_points.decode('utf-8')}",
                color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.command()
    @check_registery
    async def summary(self, ctx, *args):
        
        """ Summary of a user (or your registered user if nothing is passed)
          by calling .summary <league_name> or just .summary"""
        async with ctx.typing():
            try:
                count = 5
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

    @commands.command()
    @check_registery
    async def clash(self, ctx, *args):
        """
            Returns the opgg of all members in the same clash team as the given summoner name
        """
        async with ctx.typing():
            summoner = "".join(args)
            message = ""
            embed = False
            try:
                if len(args) != 0:
                    opgg = await self.riot_api.get_clash_opgg(summoner)
                    message = opgg
                    embed = True
                else:
                    message = "Pls provide a valid summoner name: .clash <summoner name>"
            except aiohttp.ClientResponseError as e:
                if e.status >= 400 and e.status <=500:
                    message = "Bad request error, invalid summoner"
                else:
                    message = "Internal Server Error"
            finally:
                if embed:
                    embed = discord.Embed(title=f"Clash team opgg for player: {summoner}\n\n", description=f"{message}",
                                          color=0xFF0000)
                    await ctx.send(embed=embed)
                else:
                    if message == "":
                        message = "Player is not in a clash team"
                    await ctx.send(message)
        
    @commands.command()
    @check_registery
    @mod_check
    async def add(self, ctx, option: str, *args):
        """Adds an image to the 1/100 roll, use with the discord file system (and using .add image before) or by using .add image <url>"""
        if option == 'image':
            filepath = os.path.join(os.path.dirname(__file__), '..', 'assets', 'menno_dogs', f'{str(uuid.uuid4())}.jpg')
            if ctx.message.attachments and ctx.message.attachments[0].url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                attachment_filename = ctx.message.attachments[0].filename
                await ctx.message.attachments[0].save(filepath) # doesnt work with relative paths
                await ctx.send(f'Image added: {attachment_filename}')
            elif args[-1].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                try:
                    async with aiohttp.ClientSession() as session:
                        print(args[-1])
                        async with session.get(f"{args[-1]}") as response:
                            response.raise_for_status()
                            data = await response.read()
                            with open(filepath, 'wb') as handler:
                                handler.write(data)
                            await ctx.send(f'Image added: {args[-1]}')
                except aiohttp.ClientResponseError as e:
                    ctx.send(e)
            else:
                await ctx.send('No valid image attached. Please attach an image using `.add image`. Links either ending in jpg/png/jpeg or embedded pictures.')
        elif option == 'strike':
            mentions = ctx.message.mentions
            if len(mentions) == 0:
                await ctx.send("Mention someone to strike e.g. .add strike <@319921436519038977> for being a BOTTOM G")
            else:
                for mention in mentions:
                    filtered_args = [arg for arg in list(args) if str(mention.id) not in arg]
                    if len(filtered_args) == 0:
                        # if we didnt pass a reason
                        filtered_args.append("No reason")
                    if self.redisdb.check_user_existence(mention.id) == 1:
                        total = self.redisdb.increment_field(mention.id, "strikes", 1)
                        if total >= 3:
                            success = self.redisdb.set_user_field(mention.id, "strikes", 0)
                            if success == 0:
                                user = ctx.guild.get_member(mention.id)
                                for current_role in user.roles:
                                    if current_role.name == "@everyone":
                                        continue
                                    await user.remove_roles(current_role)
                                jail_role = ctx.guild.get_role(self.jail_role)
                                await ctx.send(f"YOU EARNED A STRIKE <@{mention.id}> for {' '.join(filtered_args)} BRINGING YOU TO {total} STRIKES WHICH MEANS YOU'RE OUT , WELCOME TO MAXIMUM SECURITY JAIL {jail_role.mention}")
                                await user.add_roles(jail_role)
                            else:
                                await ctx.send(f"Couldnt reset your strikes, contact an admin")
                        else:
                            await ctx.send(f"YOU EARNED A STRIKE <@{mention.id}> for {' '.join(filtered_args)}\n TOTAL COUNT: {total}")
                    else:
                        await ctx.send(f"You cannot strike <@{mention.id}> because (s)he has not registered yet, <@{mention.id}> please use .register <your_league_name>")

        else:
            await ctx.send('Invalid option. Available options: image, text')
async def setup(bot):
    settings = Settings()
    redisDB = cacheDB(settings.REDISURL)
    riot_api = riotAPI(settings.RIOTTOKEN)
    print("adding commands...")
    await bot.add_cog(leagueCommands(bot, redisDB, riot_api, settings.JAILROLE, settings.PLAYERROLE, settings.GROLE))