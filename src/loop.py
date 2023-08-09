from discord.ext import commands, tasks
import discord
from riot import riotAPI
from database import cacheDB
from config import Settings
from redis.exceptions import ConnectionError
import aiohttp
import asyncio
class loops(commands.Cog):
    def __init__(self, bot, redis_db, riot_api, channel_id) -> None:
        self.bot: commands.bot.Bot = bot
        self.redis_db: cacheDB = redis_db
        self.riot_api: riotAPI = riot_api
        self.channel_id: int = channel_id
        self.old_active_game: int = 0
        self.active_game: int = 0
        self.active_user = "nightlon"


    @commands.Cog.listener()
    async def on_ready(self):
        self.send_message.start()
        self.active_game_searcher.start()
        self.active_game_finisher.start()

    @tasks.loop(hours=72)
    async def send_message(self):
        print("looping")
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        async with channel.typing():
            try:
                discord_ids: list[bytes] = self.redis_db.get_all_users()
            except ConnectionError as e:
                print(e)
                await channel.send("No connection to DB")

            if len(discord_ids) > 0:
                discord_ids = [id.decode('utf-8') for id in discord_ids]
            else:
                await channel.send("No users registered")
                return
            embed = discord.Embed(title="⏰ ITS EXPOSING TIME ⏰\n\n",
                                description="BOTTOM G's WILL BE REPRIMANDED",
                                color=0xFF0000)
            inters = 0
            for index, discord_id in enumerate(discord_ids):
                riot_id = self.redis_db.get_user_field(discord_id, "puuid")
                try:
                    flame_text = await self.riot_api.get_bad_kda_by_puuid(riot_id.decode('utf-8'), 5, sleep_time=5)
                except aiohttp.ClientResponseError as e:
                    print(e.message)
                    channel.send(e.message)

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

    @tasks.loop(minutes=1.0)
    async def active_game_searcher(self):
        print("active_game_searcher")
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        (active, data) = await self.riot_api.get_active_game_status(self.active_user)
        if not active or data[0][0] == self.active_game or data[0][0] == self.old_active_game:
            return
        message: discord.Message = None
        async with channel.typing():
            self.active_game = data[0][0]
            embed = discord.Embed(title=":skull::skull:  JEROEN IS IN GAME :skull::skull:\n"
                                        "YOU HAVE 60 SECONDS TO PREDICT!!!\n\n",
                                  description="HE WILL SURELY WIN, RIGHT?",
                                  color=0xFF0000)
            for team in data[1]:
                for player in team:
                    embed.add_field(name=player[0], value=f"{player[1]}: {player[2]}\n", inline=True)
                embed.add_field(name='\u200b', value='\u200b')
            if channel is not None:
                try:
                    message = await channel.send(embed=embed)
                    await message.add_reaction("🟦")
                    await message.add_reaction("🟥")
                    print("Message sent successfully.")
                except discord.Forbidden:
                    print("I don't have permission to send messages to that channel.")
                except discord.HTTPException:
                    print("Failed to send the message.")
        if message is None:
            return
        await asyncio.sleep(60)
        async with channel.typing():
            message_id = message.id
            message = await channel.fetch_message(message_id)
            await message.fetch()
            reactions = message.reactions
            text = ""
            for reaction in reactions:
                if reaction.emoji == "🟦":
                    text += "**🟦 BELIEVERS**: "
                    async for user in reaction.users():
                        if user.id != message.author.id:
                            text += f"{user} "
                    text += "\n"
                if reaction.emoji == "🟥":
                    text += "**🟥 DOUBTERS**: "
                    async for user in reaction.users():
                        if user.id != message.author.id:
                            text += f"{user} "
            try:
                await channel.send(text)
                print("Message sent successfully.")
            except discord.Forbidden:
                print("I don't have permission to send messages to that channel.")
            except discord.HTTPException:
                print("Failed to send the message.")

    @tasks.loop(minutes=1.0)
    async def active_game_finisher(self):
        print("active_game_finisher")
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        if self.active_game == 0:
            return
        match_id = f'EUW1_{self.active_game}'
        try:
            match_data = await self.riot_api.get_match_details_by_matchID(match_id)
        except aiohttp.ClientResponseError:
            # Game is still in progress
            return
        result = False
        for player in match_data:
            if player['summonerName'].lower() == self.active_user.lower():
                result = player['win']
        text = ""
        if result:
            text = "**BELIEVERS WIN!!! HE HAS DONE IT AGAIN, THE 👑**"
        else:
            text = "**DOUBTERS WIN!!! UNLUCKY, BUT SURELY NOT HIS FAULT 💀**"
        self.old_active_game = self.active_game
        self.active_game = 0
        if channel is not None:
            try:
                await channel.send(text)
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