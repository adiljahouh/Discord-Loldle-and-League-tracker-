
from PIL import Image, ImageDraw, ImageFont
from discord import Member
import discord
import aiohttp
from io import BytesIO

# Fetch the profile picture
async def get_profile_pic(member: Member):
    avatar_url = member.avatar.url  # .avatar is a shortcut for .avatar_url in discord.py v2.x+
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            if resp.status == 200:
                img_data = await resp.read()
                img = Image.open(BytesIO(img_data))
                return img
            else:
                return None

async def draw_dead_or_alive(base_image_path: str, profile_pic: Image, font_path: str, lifetimestrikes: int):
    # Open the base image (ensure it's RGBA for transparency)
    base_image = Image.open(base_image_path)
    if profile_pic is None:
        # If no profile picture is provided, return the base image as bytes
        buffer = BytesIO()
        base_image.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer
    print(profile_pic.size)
    target_width, target_height = 1428, 1033
    profile_pic = profile_pic.resize(
        (target_width, target_height), Image.Resampling.BOX
    )

        # Paste the profile picture inside the transparent block
    base_image.paste(profile_pic, (163, 532), profile_pic)
    # Load a font
    font = ImageFont.truetype(font_path, size=140)  # Replace with the desired font

    sample_color = base_image.getpixel((80, 150))
    text = f"BOUNTY ${1000*lifetimestrikes}"
    draw = ImageDraw.Draw(base_image)

    text_bbox = draw.textbbox((0, 0), text, font=font)  # Top-left corner doesn't matter here
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    width, height = base_image.size
    x = (width - text_width) // 2

    draw.text((x, 1900), text, fill=sample_color, font=font)
    # Save the combined image to a BytesIO buffer
    buffer = BytesIO()
    base_image.save(buffer, format="JPEG")
    buffer.seek(0)  # Move the pointer to the beginning of the buffer

    return buffer

