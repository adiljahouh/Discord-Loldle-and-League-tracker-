import aiohttp
from discord.ext import commands
from config import Settings
import discord
import os
import random
import uuid
from commands.utility.decorators import role_check, mod_check
from api.animals import cat_api, dog_api, duck_api, frog_api


class AnimalCommands(commands.Cog):
    def __init__(self, jail_role_id: int, player_role_id: int, g_role: int) -> None:
        self.jail_role = jail_role_id
        self.player_role = player_role_id
        self.g_role = g_role

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command()
    @role_check
    async def duck(self, ctx: commands.Context):
        """
            Returns a duck pic or gif
        """
        # TODO: add retry logic
        async with ctx.typing():
            if random.randint(0, 100) == 1:
                img = random.choice(os.listdir('./assets/menno_dogs'))
                await ctx.send("@here A VERY GOOD BOY APPEARS", file=discord.File(f'./assets/menno_dogs/{img}'))
            else:
                message = await duck_api()
                await ctx.send(message)

    @commands.command()
    @role_check
    async def dog(self, ctx: commands.Context):
        """
            Returns a dog pic
        """
        # TODO: add retry logic
        async with ctx.typing():
            if random.randint(0, 100) == 1:
                img = random.choice(os.listdir('./assets/menno_dogs'))
                await ctx.send("@here A VERY GOOD BOY APPEARS", file=discord.File(f'./assets/menno_dogs/{img}'))
            else:
                message = await dog_api()
                await ctx.send(message)

    @commands.command()
    @role_check
    async def cat(self, ctx: commands.Context):
        """
            Returns a cat pic
        """
        # TODO: add retry logic
        async with ctx.typing():
            if random.randint(0, 100) == 1:
                img = random.choice(os.listdir('./assets/menno_dogs'))
                await ctx.send("@here A VERY GOOD BOY APPEARS", file=discord.File(f'./assets/menno_dogs/{img}'))
            else:
                message = await cat_api()
                await ctx.send(message)

    @commands.command()
    @role_check
    async def frog(self, ctx: commands.Context):
        """
            Returns a frog pic
        """
        # TODO: add retry logic
        async with ctx.typing():
            if random.randint(0, 100) == 1:
                img = random.choice(os.listdir('./assets/menno_dogs'))
                await ctx.send("@here A VERY GOOD BOY APPEARS", file=discord.File(f'./assets/menno_dogs/{img}'))
            else:
                message = await frog_api()
                await ctx.send(message)

    @commands.command()
    @role_check
    async def drog(self, ctx: commands.Context):
        """
            Returns a drog, who the fuck knows what that is
        """
        # TODO: add retry logic
        async with ctx.typing():
            try:
                img = random.choice(os.listdir('./assets/drog'))
                await ctx.send(file=discord.File(f'./assets/drog/{img}'))
            except Exception as e:
                print(e)
                await ctx.send("Something wrong with getting the image")

    @commands.command()
    @role_check
    @mod_check
    async def image(self, ctx: commands.Context, *args):
        """Adds an image to the 1/100 roll, use with the discord file system by using .image or by using .image <url>"""
        filepath = f"./assets/menno_dogs/{str(uuid.uuid4())}.jpg"
        if ctx.message.attachments and ctx.message.attachments[0].url.lower().split("?", 1)[0].endswith(
                ('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            attachment_filename = ctx.message.attachments[0].filename
            await ctx.message.attachments[0].save(filepath)  # doesnt work with relative paths
            await ctx.send(f'Image added: {attachment_filename}')
        elif args[-1].lower().split("?", 1)[0].endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
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


async def setup(bot: commands.Bot):
    settings = Settings()
    print("adding animal commands...")
    await bot.add_cog(AnimalCommands(settings.JAILROLE, settings.PLAYERROLE, settings.GROLE))
