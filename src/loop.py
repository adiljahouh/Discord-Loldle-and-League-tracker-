from discord.ext import commands, tasks
import discord
import os
from riot import riotAPI
from database import cacheDB
from dotenv import load_dotenv
class loops(riotAPI, commands.Cog):
    def __init__(self, bot, redisdb) -> None:
        self.bot = bot
        load_dotenv()
        self.redisdb: cacheDB = redisdb
        self.RIOTTOKEN = os.getenv("RIOTTOKEN")
        super().__init__(self.RIOTTOKEN)
    

    @commands.Cog.listener()
    async def on_ready(self):
        await self.send_message.start()

    @tasks.loop(hours=10)
    async def send_message(self):
        print("looping")
        # user = self.bot.users # get all users
        channel_id: int = self.bot.CHANNEL_ID 
        channel = self.bot.get_channel(channel_id)
        discord_ids: list[bytes] = self.redisdb.get_all_users()
        if len(discord_ids) > 0:
            discord_ids = [id.decode('utf-8') for id in discord_ids]
        else:
            return
        embed = discord.Embed(title="⏰ ITS EXPOSING TIME ⏰\n\n", 
                              description="BOTTOM G's WILL BE REPRIMANDED",
                              color=0xFF0000)
        for index, discord_id in enumerate(discord_ids):
            print("discord id ", discord_id)
            riot_id = self.redisdb.get_user_field(discord_id, "puuid")
            flame_text = super().get_bad_kda_by_puuid(riot_id.decode('utf-8'))
            if flame_text:
                embed.add_field(name = f"SUSPECT #{index+1}", value=f"<@{discord_id}>\n {flame_text}\n")


        if channel is not None:
            """
            query redis db for all users, check recents kdas and retrieve the cumulative worst.
            
            """
            try:
                # await channel.send(embed=embed)
                print("Message sent successfully.")
            except discord.Forbidden:
                print("I don't have permission to send messages to that channel.")
            except discord.HTTPException:
                print("Failed to send the message.")

async def setup(bot):
    redisDB: cacheDB = cacheDB(os.getenv("REDISURL"))
    print("adding loops..")
    await bot.add_cog(loops(bot, redisDB))