import random
from PIL import Image, ImageOps, ImageFilter
import io
import discord
import discord.ext.commands
from api.ddragon import get_random_skin_splash, get_random_spell
from commands.utility.get_closest_word import find_closest_name
import asyncio
from databases.loldle import loldleDB

import discord.ext
champ_base_data = {}
async def blur_invert_image(image_content):
    # Open the image from the binary content
    image = Image.open(io.BytesIO(image_content))
    
    # Convert the image to grayscale
    color_inverted_image = ImageOps.equalize(image, mask = None)
    blurred_image = color_inverted_image.filter(ImageFilter.BLUR)
    # Rotate the grayscale image by 90 degrees
    rotation_angle = random.choice([90, 180, 270])
    
    # Rotate the grayscale image by the chosen angle
    rotated_image = blurred_image.rotate(rotation_angle)
    
    # Save the transformed image to a bytes-like object
    output_stream = io.BytesIO()
    rotated_image.save(output_stream, format="PNG")
    
    return output_stream.getvalue()

async def crop_image(image_content, percentage = 10):
    # Open the image from the binary content
    image = Image.open(io.BytesIO(image_content))
    
    # # Convert the image to grayscale
    # grayscale_image = ImageOps.grayscale(image)

    # Get the dimensions of the image
    width, height = image.size


    # Calculate the crop dimensions for the middle 10%
    crop_percentage = percentage / 100.0
    crop_left = width * (0.5 - crop_percentage / 2)
    crop_upper = height * (0.5 - crop_percentage / 2)
    crop_right = width * (0.5 + crop_percentage / 2)
    crop_lower = height * (0.5 + crop_percentage / 2)

    # Crop the image to the calculated dimensions
    cropped_image = image.crop((crop_left, crop_upper, crop_right, crop_lower))
    
    # Save the transformed image to a bytes-like object
    output_stream = io.BytesIO()
    cropped_image.save(output_stream, format="PNG")
    
    return output_stream.getvalue()


def compare_dicts_and_create_text(dict1, dict2)-> tuple:
    cross_emoji = "❌"
    check_emoji = "✅"
    up_arrow_emoji = "⬆️"
    down_arrow_emoji = "⬇️"
    result_text = ""
    
    # Initialize a flag to track if all values match
    all_values_match = True

    # Compare the dictionaries
    for key in dict1:
        if key in dict2:
            if isinstance(dict1[key], list) and isinstance(dict2[key], list):
                # Both values are lists, compare items
                matching_items = [f"{check_emoji} {item}" for item in dict1[key] if item in dict2[key]]
                non_matching_items = [f"{cross_emoji} {item}" for item in dict1[key] if item not in dict2[key]]
                if non_matching_items:
                    all_values_match = False  # Set flag to False if there are non-matching items
                items_str = ' '.join(matching_items + non_matching_items)
                result_text += f"{key}: {items_str}\n"
            elif dict1[key] == dict2[key]:
                # Values match
                result_text += f"{key}: {check_emoji} {dict1[key]}\n"
            elif key == "ReleaseDate":
                # Values don't match and key is releaseDate
                if float(dict1[key]) > float(dict2[key]):
                    result_text += f"{key}: {down_arrow_emoji} {dict1[key]}\n"
                else:
                    result_text += f"{key}: {up_arrow_emoji} {dict1[key]}\n"
                all_values_match = False
            else:
                # Values don't match
                result_text += f"{key}: {cross_emoji} {dict1[key]}\n"
                all_values_match = False
        else:
            # Key doesn't exist in the second dictionary
            result_text += f"{key}: {cross_emoji} {dict1[key]} -> Key not found\n"
            all_values_match = False

    return (all_values_match, result_text.strip())



class loldleView(discord.ui.View):
    def __init__(self, *, timeout = 200, ctx: discord.ext.commands.Context, champ_list, bot, main_db, day,
                  winning_guess_info, loldle_db: loldleDB, ddrag_version):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = bot
        self.champ_list = champ_list
        self.correct_guess = False
        self.attempts = 0
        self.max_attempts = 10  # Set the maximum number of attempts here
        self.max_points = 2000
        self.main_db = main_db
        self.day = day
        self.winning_guess_info = winning_guess_info
        self.loldle_db = loldle_db
        self.ddrag_version = ddrag_version

    def check(self, m: discord.Message):
        return m.author == self.ctx.author and m.channel == self.ctx.channel
    
    async def compare_result(self):
        msg = await self.bot.wait_for('message', check=self.check, timeout=90.0)
        champion_guess = (msg.content.replace(" ", "")).capitalize()
        score_and_ddrag_name = find_closest_name(champion_guess, self.champ_list)
        print(score_and_ddrag_name)
        ddrag_name = score_and_ddrag_name[0]
        # await ctx.send(f"Your guess has been converted to {ddrag_name}")
        try:
            champion_guess_info = self.loldle_db.get_champion_info(champion_name=ddrag_name)
            champion_guess_info.pop("timestamp")
            is_match_and_text = compare_dicts_and_create_text(champion_guess_info, self.winning_guess_info)
            mention_and_text = is_match_and_text[1] + f"\n<@{str(self.ctx.author.id)}>"
            # await self.ctx.send(mention_and_text)
            await msg.reply(is_match_and_text[1])
            if is_match_and_text[0]:
                self.correct_guess = True
        except Exception as e:
            await self.ctx.send(e)

    
    
    @discord.ui.button(label="Classic", 
                       style=discord.ButtonStyle.green)
    async def start_classic_loldle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.ctx.author:
            try:
                await interaction.response.defer() 
                self.stop()
                self.attempts = 0
                self.max_attempts = 10  # Set the maximum number of attempts here
                self.max_points = 2000
                status = f"Guess a champion and win {self.max_points} points, for each guess wrong you lose {int(self.max_points/self.max_attempts)} points. Not replying for over 90 seconds will close the game.\n\nStart the game by guessing a champ <@{str(self.ctx.author.id)}>."
                await interaction.followup.send(status)
                while not self.correct_guess and self.attempts < self.max_attempts:
                    self.attempts += 1
                    try:
                        await self.compare_result()
                    except asyncio.TimeoutError:
                        result = f'You took too long to respond, the champion was {self.winning_guess_info["Name"]}... Your game ended <@{str(self.ctx.author.id)}>.'
                        self.ctx.send(result)
                        self.main_db.set_user_field(str(self.ctx.author.id), "last_loldle", self.day.strftime('%Y-%m-%d'))
                        break
                
                if self.correct_guess:
                    points =int(self.max_points - ((self.attempts-1)*(self.max_points/self.max_attempts)))
                    result = f"Correct guess! You earned {points} points <@{str(self.ctx.author.id)}>"
                else:
                    points = 0
                    result = f"Incorrect, the champion was {self.winning_guess_info['Name']}. You earned {points} points <@{str(self.ctx.author.id)}>"

                self.main_db.increment_field(str(self.ctx.author.id), "points", points)
                self.main_db.set_user_field(str(self.ctx.author.id), "last_loldle", self.day.strftime('%Y-%m-%d'))
                await self.ctx.send(result)
            except Exception as e:
                print(e)
            
        else:
            await interaction.response.send_message("That's not your Loldle", ephemeral=True)


    @discord.ui.button(label="Ability", 
                       style=discord.ButtonStyle.blurple)
    async def start_ability_loldle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.ctx.author:
            try:
                await interaction.response.defer()
                self.stop() 
                self.attempts = 0
                self.max_attempts = 5  # Set the maximum number of attempts here
                self.max_points = 2000
                status = f"Guess a champion and win {self.max_points} points, for each guess wrong you lose {int(self.max_points/self.max_attempts)} points. Not replying for over 90 seconds will close the game.\n\nStart the game by guessing a champ <@{str(self.ctx.author.id)}> based on the image below: \n"

                ability_image = await get_random_spell(self.ddrag_version, self.winning_guess_info['Name'])
                transformed_image =  await blur_invert_image(ability_image)
                await interaction.followup.send(status, file=discord.File(io.BytesIO(transformed_image), f"idk.png"))
                while not self.correct_guess and self.attempts < self.max_attempts:
                    self.attempts += 1
                    try:
                        await self.compare_result()
                    except asyncio.TimeoutError:
                        result = f'You took too long to respond, the champion was {self.winning_guess_info["Name"]}... Your game ended <@{str(self.ctx.author.id)}>.'
                        self.main_db.set_user_field(str(self.ctx.author.id), "last_loldle", self.day.strftime('%Y-%m-%d'))
                        break
                
                if self.correct_guess:
                    points =int(self.max_points - ((self.attempts-1)*(self.max_points/self.max_attempts)))
                    result = f"Correct guess! You earned {points} points <@{str(self.ctx.author.id)}>"
                else:
                    points = 0
                    result = f"Incorrect, the champion was {self.winning_guess_info['Name']}. You earned {points} points <@{str(self.ctx.author.id)}>"

                self.main_db.increment_field(str(self.ctx.author.id), "points", points)
                self.main_db.set_user_field(str(self.ctx.author.id), "last_loldle", self.day.strftime('%Y-%m-%d'))
                await self.ctx.send(result, file=discord.File(io.BytesIO(ability_image), f"real.png"))
            except Exception as e:
                print(e)
        else:
            await interaction.response.send_message("That's not your Loldle", ephemeral=True)


    @discord.ui.button(label="Splash", 
                       style=discord.ButtonStyle.red)
    async def start_splash_loldle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user == self.ctx.author:
            try:
                await interaction.response.defer()
                self.stop() 
                self.attempts = 0
                self.max_attempts = 5  # Set the maximum number of attempts here
                self.max_points = 2000
                status = f"Guess a champion and win {self.max_points} points, for each guess wrong you lose {int(self.max_points/self.max_attempts)} points. After each 2 wrong guesses you will get a hint.\n Not replying for over 90 seconds will close the game.\n\nStart the game by guessing a champ <@{str(self.ctx.author.id)}> based on the image below: \n"
                splash_image = await get_random_skin_splash(self.ddrag_version, self.winning_guess_info['Name'])
                transformed_image =  await crop_image(splash_image)
                await interaction.followup.send(status, file=discord.File(io.BytesIO(transformed_image), f"idk.png"))
                while not self.correct_guess and self.attempts < self.max_attempts:
                    if self.attempts == 2:
                        easier_image = await crop_image(splash_image, percentage=20)
                        await self.ctx.send("Hint\n", file=discord.File(io.BytesIO(easier_image), f"hint.png"))
                    self.attempts += 1
                    try:
                        await self.compare_result()
                    except asyncio.TimeoutError:
                        result = f'You took too long to respond, the champion was {self.winning_guess_info["Name"]}... Your game ended <@{str(self.ctx.author.id)}>.'
                        self.main_db.set_user_field(str(self.ctx.author.id), "last_loldle", self.day.strftime('%Y-%m-%d'))
                        break
                if self.correct_guess:
                    points =int(self.max_points - ((self.attempts-1)*(self.max_points/self.max_attempts)))
                    result = f"Correct guess! You earned {points} points <@{str(self.ctx.author.id)}>"
                else:
                    points = 0
                    result = f"Incorrect, the champion was {self.winning_guess_info['Name']}. You earned {points} points <@{str(self.ctx.author.id)}>"

                self.main_db.increment_field(str(self.ctx.author.id), "points", points)
                self.main_db.set_user_field(str(self.ctx.author.id), "last_loldle", self.day.strftime('%Y-%m-%d'))
                await self.ctx.send(result, file=discord.File(io.BytesIO(splash_image), f"real.png"))
            except Exception as e:
                print(e)
        else:
            await interaction.response.send_message("That's not your Loldle", ephemeral=True)
