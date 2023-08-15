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
        self.active_message_id: discord.Message.id = 0
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
        embed = None
        async with channel.typing():
            self.active_game = data[0][0]
            embed = discord.Embed(title=":skull::skull:  JEROEN IS IN GAME :skull::skull:\n"
                                        "YOU HAVE 5 MINUTES TO PREDICT!!!\n\n",
                                  description="HE WILL SURELY WIN, RIGHT?",
                                  color=0xFF0000)
            embed_fields = []
            for indx, team in enumerate(data[1]):
                embed_fields.append("")
                for player in team:
                    embed_fields[indx] += f"**{player[2]}** ({player[1]})\n"
            embed.add_field(name="🟦", value=embed_fields[0], inline=True)
            embed.add_field(name='\u200b', value='\u200b', inline=True)
            embed.add_field(name="🟥", value=embed_fields[1], inline=True)

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
        await asyncio.sleep(300)
        async with channel.typing():
            message_id = message.id
            self.active_message_id = message_id
            message_update = await channel.fetch_message(message_id)
            await message_update.fetch()
            reactions = message_update.reactions
            text = ""
            for reaction in reactions:
                if reaction.emoji == "🟦":
                    async for user in reaction.users():
                        if user.id != message_update.author.id:
                            text += f"{user} "
                    embed.add_field(name="**🟦 BELIEVERS**", value=text, inline=True)
                    embed.add_field(name='\u200b', value='\u200b')
                    embed.add_field(name='\u200b', value='\u200b')
                text = ""
                if reaction.emoji == "🟥":
                    async for user in reaction.users():
                        if user.id != message_update.author.id:
                            text += f"{user} "
                    embed.add_field(name="**🟥 DOUBTERS**", value=text, inline=True)
                    embed.add_field(name='\u200b', value='\u200b')
                    embed.add_field(name='\u200b', value='\u200b')
            try:
                await message_update.edit(embed=embed)
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
        score = ""
        for player in match_data:
            if player['summonerName'].lower() == self.active_user.lower():
                result = player['win']
                score = f"{player['kills']} / {player['deaths']} / {player['assists']}, bait pings: {player['baitPings']}"
        text = ""
        if result:
            text = "**BELIEVERS WIN!!! HE HAS DONE IT AGAIN, THE 👑**\n"
        else:
            text = "**DOUBTERS WIN!!! UNLUCKY, BUT SURELY NOT HIS FAULT 💀**\n"
        text += score
        self.old_active_game = self.active_game
        self.active_game = 0
        if channel is not None:
            message = await channel.fetch_message(self.active_message_id)
            embed = message.embeds[0]
            embed.add_field(name="RESULT!!!", value=text, inline=True)
            try:
                await message.edit(embed=embed)
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