from discord.ext import commands, tasks
import discord
from api.riot import riotAPI
from config import Settings
from commands.utility.team_image import imageCreator
from redis.exceptions import ConnectionError
import aiohttp
import asyncio
from databases.betting_db import BettingDB
from databases.main_db import MainDB
from databases.stalking_db import StalkingDB
from commands.utility.end_image import EndImage


class loops(commands.Cog):
    def __init__(self, bot, main_db, betting_db, stalking_db, riot_api, channel_id, ping_role) -> None:
        self.bot: commands.bot.Bot = bot
        self.main_db = main_db
        self.betting_db = betting_db
        self.stalking_db = stalking_db
        self.riot_api: riotAPI = riot_api
        self.channel_id: int = channel_id
        self.ping_role = ping_role
        self.victim = ""

    @commands.Cog.listener()
    async def on_ready(self):
        self.activate_stalking.start()
        self.done_stalking.start()
        self.leaderboard.start()
        await asyncio.sleep(36000)  # 1800
        self.send_message.start()

    @tasks.loop(hours=24)
    async def send_message(self):
        print("Setting up exposing session...")
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        async with channel.typing():
            try:
                discord_ids: list[bytes] = self.main_db.get_all_users()
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
                riot_id = self.main_db.get_user_field(discord_id, "puuid")
                try:
                    flame_text = await self.riot_api.get_bad_kda_by_puuid(riot_id.decode('utf-8'), 5, sleep_time=10)
                except aiohttp.ClientResponseError as e:
                    print(e.message)
                    await channel.send(e.message)
                    return

                if flame_text:
                    inters += 1
                    embed.add_field(name=f"SUSPECT #{inters}", value=f"<@{discord_id}>\n {flame_text}\n")

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
    # FIXME: Remove the concurrency here, its redundant
    async def leaderboard(self):
        """
            Keeps track of top 5 in each role of the leaderboard
        """
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        async with channel.typing():
            print("Retrieving Leaderboard...")
            try:
                discord_ids: list[bytes] = self.main_db.get_all_users()
            except ConnectionError as e:
                await channel.send("Could not connect to database.")
                return
            leaderboard_text = ''
            if len(discord_ids) > 0:
                discord_ids = [id.decode('utf-8') for id in discord_ids]
            else:
                await channel.send("No users are registered.")
            tasks = []
            delay = 1
            for discord_id in discord_ids:
                puuid = self.main_db.get_user_field(discord_id, "puuid")
                tasks.append(self.riot_api.get_highest_damage_taken_by_puuid(puuid=puuid.decode('utf-8'), count=5,
                                                                             sleep_time=delay, discord_id=discord_id))
                delay += 10
            try:
                result = await asyncio.gather(*tasks)
            except aiohttp.ClientResponseError as e:
                print(e)
                await channel.send(e.message + ', please wait a minute.')
                return
            top_5 = sorted(result, key=lambda x: x['taken'], reverse=True)[:5]
            for index, top_g in enumerate(top_5):
                leaderboard_text += f'\n{index + 1}. <@{top_g["disc_id"]}> | {top_g["taken"]} on **{top_g["champion"]}**'
            description = f"Type .register to be able to participate"
            embed = discord.Embed(title="💪🏽TOPPEST G's💪🏽\n\n", description=f"{description}", color=0xFF0000)
            embed.add_field(name="Top Damage Taken Past 5 Games", value=leaderboard_text)
            await channel.send(embed=embed)

    @tasks.loop(minutes=1.0)
    async def activate_stalking(self):
        print("Activate_stalking")
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        try:
            # Check if a user is currently getting stalked
            if self.stalking_db.get_active_user() is not None:
                return
            victims = self.stalking_db.get_all_users()
            print(victims)
            found = False
            active = False
            data = None
            for victim in victims:
                try:
                    (active, data) = await self.riot_api.get_active_game_status(victim)
                    print(f"{victim}: {active}")
                except aiohttp.ClientResponseError as e:
                    # print(victim, " Failed to get active game status with error: ", e)
                    continue
                if active:
                    self.victim = victim
                    found = True
                    break
            if not found:
                print("No active user was found")
                return
            message = None
            embed = None
            async with channel.typing():
                embed = discord.Embed(title=f":skull::skull:  {self.victim.upper()} IS IN GAME :skull::skull:\n"
                                            "YOU HAVE 10 MINUTES TO PREDICT!!!\n\n",
                                      description="HE WILL SURELY WIN, RIGHT?",
                                      color=0xFF0000)
                champions = [[player[1] for player in team] for team in data[1]]
                players = [[player[0] for player in team] for team in data[1]]
                try:
                    image_creator: imageCreator = imageCreator(champions, players, data[2])
                    img = await image_creator.get_team_image()
                except aiohttp.ClientResponseError as e:
                    print("Failed to get images for image creator with exception: ", e)
                    return
                picture = discord.File(fp=img, filename="team.png")
                embed.set_image(url="attachment://team.png")

                if channel is not None:
                    try:
                        if data[2] != "Custom":
                            self.betting_db.enable_betting()
                            message = await channel.send(f"<@&{self.ping_role}>", file=picture, embed=embed)
                        else:
                            message = await channel.send(file=picture, embed=embed)
                        print("Message sent successfully.")
                    except Exception as e:
                        print(e)
                        return
            # TODO: Set the user status to True
            # TODO: Set the active game
            if data[2] == "Custom":
                return
            await asyncio.sleep(self.betting_db.betting_time)
            async with channel.typing():
                all_bets = self.betting_db.get_all_bets()
                for decision in all_bets.keys():
                    text = ""
                    for user in all_bets[decision]:
                        text += f"{user['name']} **{user['amount']}**\n"
                    embed.add_field(name=f"**{decision.upper()}**", value=text, inline=True)
                    if decision == "believers":
                        embed.add_field(name='\u200b', value='\u200b')
                try:
                    await message.edit(embed=embed)
                    embed = discord.Embed(title="Betting is no longer enabled",
                                          color=0xFF0000)
                    await channel.send(embed=embed)
                    print("Message sent successfully.")
                except Exception as e:
                    print(e)
        # Send the error in Discord
        except Exception as e:
            try:
                await channel.send(f"{e}")
            except Exception as e:
                print(e)

    






async def setup(bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    betting_db = BettingDB(settings.REDISURL)
    stalking_db = StalkingDB(settings.REDISURL)
    riot: riotAPI = riotAPI(settings.RIOTTOKEN)
    print("adding loops..")
    await bot.add_cog(loops(bot, main_db, betting_db, stalking_db, riot, settings.CHANNELID, settings.PINGROLE))
