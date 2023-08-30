from discord.ext import commands, tasks
import discord
from riot import riotAPI
from database import cacheDB
from config import Settings
from team_image import imageCreator
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
        self.active_game_searcher.start()
        self.active_game_finisher.start()
        self.leaderboard.start()
        await asyncio.sleep(36000) #1800
        self.send_message.start()

    @tasks.loop(hours=24)
    async def send_message(self):
        print("Setting up exposing session...")
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
                    flame_text = await self.riot_api.get_bad_kda_by_puuid(riot_id.decode('utf-8'), 5, sleep_time=10)
                except aiohttp.ClientResponseError as e:
                    print(e.message)
                    await channel.send(e.message)
                    return

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


    @tasks.loop(hours=24)
    #FIXME: Remove the concurrency here, its redundant
    async def leaderboard(self):  
        """
            Keeps track of top 5 in each role of the leaderboard
        """
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        async with channel.typing():
            print("Retrieving Leaderboard...")
            try:
                discord_ids: list[bytes] = self.redis_db.get_all_users()
            except ConnectionError as e:
                await channel.send("Could not connect to database.")
                return
            leaderboard_text = ''
            if len(discord_ids) > 0:
                discord_ids = [id.decode('utf-8') for id in discord_ids]
            else:
                await channel.send("No users are registered.")
            tasks= []
            delay = 1
            for discord_id in discord_ids:
                puuid = self.redis_db.get_user_field(discord_id, "puuid")
                tasks.append(self.riot_api.get_highest_damage_taken_by_puuid(puuid=puuid.decode('utf-8'), count=5, sleep_time=delay, discord_id = discord_id))
                delay += 10
            try:
                result = await asyncio.gather(*tasks)
            except aiohttp.ClientResponseError as e:
                print(e)
                await channel.send(e.message + ', please wait a minute.')
                return
            top_5 = sorted(result, key=lambda x: x['taken'], reverse=True)[:5]
            for index, top_g in enumerate(top_5):
                leaderboard_text += f'\n{index+1}. <@{top_g["disc_id"]}> | {top_g["taken"]} on **{top_g["champion"]}**'
            description = f"Type .register to be able to participate"
            embed = discord.Embed(title="💪🏽TOPPEST G's💪🏽\n\n", 
                            description=f"{description}",
                            color=0xFF0000)
            embed.add_field(name="Top Damage Taken Past 5 Games", value = leaderboard_text)
            await channel.send(embed=embed)

    @tasks.loop(minutes=1.0)
    async def active_game_searcher(self):
        print("active_game_searcher")
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        try:
            (active, data) = await self.riot_api.get_active_game_status(self.active_user)
        except aiohttp.ClientResponseError as e:
            # print("Failed to get active game status with error: ", e)
            return
        if not active or data[0] == self.active_game or data[0] == self.old_active_game:
            return
        message: discord.Message = None
        embed = None
        async with channel.typing():
            self.active_game = data[0]
            embed = discord.Embed(title=":skull::skull:  JEROEN IS IN GAME :skull::skull:\n"
                                        "YOU HAVE 10 MINUTES TO PREDICT!!!\n\n",
                                  description="HE WILL SURELY WIN, RIGHT?",
                                  color=0xFF0000)
            champions = [[player[1] for player in team] for team in data[1]]
            players = [[player[0] for player in team] for team in data[1]]
            image_creator: imageCreator = imageCreator(self.riot_api, champions, players, data[2])
            try:
                img = await image_creator.get_team_image()
            except aiohttp.ClientResponseError as e:
                print("Failed to get images for image creator with exception: ", e)
                return
            picture = discord.File(fp=img, filename="team.png")
            embed.set_image(url="attachment://team.png")

            if channel is not None:
                try:
                    message = await channel.send("@here", file=picture, embed=embed)
                    self.redis_db.enable_betting()
                    print("Message sent successfully.")
                except discord.Forbidden:
                    print("I don't have permission to send messages to that channel.")
                except discord.HTTPException:
                    print("Failed to send the message.")
        if message is None:
            return
        self.active_message_id = message.id
        await asyncio.sleep(self.redis_db.betting_time)
        async with channel.typing():
            all_bets = self.redis_db.get_all_bets()
            for decision in all_bets.keys():
                text = ""
                for user in all_bets[decision]:
                    text += f"{user['name']} **{user['amount']}**\n"
                embed.add_field(name=f"**{decision.upper()}**", value=text, inline=True)
                if decision == "believers":
                    embed.add_field(name='\u200b', value='\u200b')
            try:
                await message.edit(embed=embed)
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
            print("Game is still in progress")
            return
        result = False
        score = ""
        for player in match_data:
            if player['summonerName'].lower() == self.active_user.lower():
                result = player['win']
                score = f"{player['kills']} / {player['deaths']} / {player['assists']}, bait pings: {player['baitPings']}\n"
        if result:
            description = "**BELIEVERS WIN!!! HE HAS DONE IT AGAIN, THE 👑**\n"
            winners = "believers"
        else:
            description = "**DOUBTERS WIN!!! UNLUCKY, BUT SURELY NOT HIS FAULT 💀**\n"
            winners = "doubters"

        description += score
        message: discord.Message = await channel.fetch_message(self.active_message_id)
        embed = discord.Embed(title=":skull::skull:  JEROEN'S GAME RESULT IS IN :skull::skull:\n\n",
                              description=description,
                              color=0xFF0000)
        all_bets = self.redis_db.get_all_bets()
        for decision in all_bets.keys():
            text = ""
            decide = "won" if decision == winners else "lost"
            for user in all_bets[decision]:
                if decision == winners:
                    self.redis_db.increment_field(user['discord_id'], "points", 2*int(user['amount']))
                if decide == "won":
                    text += f"{user['name']} has {decide} {2*int(user['amount'])} points\n"
                else:
                    text += f"{user['name']} has {decide} {user['amount']} points\n"
            embed.add_field(name=f"**{decision.upper()}**", value=text, inline=True)
            if decision == "believers":
                embed.add_field(name='\u200b', value='\u200b')
        self.old_active_game = self.active_game
        self.active_game = 0
        if channel is not None:
            try:
                self.redis_db.remove_all_bets()
                await channel.send(embed=embed, reference=message)
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