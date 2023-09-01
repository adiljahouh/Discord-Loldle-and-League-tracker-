import aiohttp
from discord.ext import commands
import requests
from config import Settings
from database import cacheDB
import discord
import os
import random
import json
import uuid
from commands_utility import role_check, mod_check


class AnimalCommands(commands.Cog):
    def __init__(self, redisdb, jail_role_id, player_role_id, g_role) -> None:
        self.redisdb: cacheDB = redisdb
        self.jail_role = jail_role_id
        self.player_role = player_role_id
        self.g_role = g_role

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command()
    @role_check
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

    @commands.command()
    @role_check
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
    @role_check
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
    @role_check
    @mod_check
    async def add(self, ctx, option: str, *args):
        """Adds an image to the 1/100 roll, use with the discord file system (and using .add image before) or by using .add image <url>"""
        if option == 'image':
            filepath = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'menno_dogs', f'{str(uuid.uuid4())}.jpg')
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
    print("adding commands...")
    await bot.add_cog(AnimalCommands(redisDB, settings.JAILROLE, settings.PLAYERROLE, settings.GROLE))
