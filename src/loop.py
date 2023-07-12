from discord.ext import commands, tasks
import discord
from riot import riotAPI
from database import cacheDB
from config import Settings
class loops(commands.Cog):
    def __init__(self, bot, redis_db, riot_api, channel_id) -> None:
        self.bot: commands.bot.Bot = bot
        self.redis_db: cacheDB = redis_db
        self.riot_api: riotAPI = riot_api
        self.channel_id: int = channel_id
    

    @commands.Cog.listener()
    async def on_ready(self):
        await self.send_message.start()

    @tasks.loop(hours=24)
    async def send_message(self):
        print("looping")
        # user = self.bot.users # get all users
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        discord_ids: list[bytes] = self.redis_db.get_all_users()
        if len(discord_ids) > 0:
            discord_ids = [id.decode('utf-8') for id in discord_ids]
        else:
            await channel.send("No users registered")

        
        embed = discord.Embed(title="⏰ ITS EXPOSING TIME ⏰\n\n", 
                              description="BOTTOM G's WILL BE REPRIMANDED",
                              color=0xFF0000)
        inters = 0
        for index, discord_id in enumerate(discord_ids):
            riot_id = self.redis_db.get_user_field(discord_id, "puuid")
            flame_text =self. riot_api.get_bad_kda_by_puuid(riot_id.decode('utf-8'))
            if flame_text:
                inters+=1
                embed.add_field(name = f"SUSPECT #{inters}", value=f"<@{discord_id}>\n {flame_text}\n")


        if channel is not None:
            """
            query redis db for all users, check recents kdas and retrieve the cumulative worst.
            
            """
            try:
                await channel.send(embed=embed)
                print("Message sent successfully.")
            except discord.Forbidden:
                print("I don't have permission to send messages to that channel.")
            except discord.HTTPException:
                print("Failed to send the message.")

async def setup(bot):
    settings = Settings()
    redis_db: cacheDB = cacheDB(settings.REDISURL)
    riot: riotAPI = riotAPI(settings.RIOTTOKEN)
    print("adding loops..")
    await bot.add_cog(loops(bot, redis_db, riot, settings.CHANNELID))