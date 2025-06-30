from discord.ext import commands, tasks
import discord
from api.riot import riotAPI
from config import Settings
from commands.utility.team_image import imageCreator
from redis.exceptions import ConnectionError
import aiohttp
import asyncio
from databases.betting import BettingDB
from databases.main import MainDB
from databases.stalker import StalkingDB
from commands.utility.end_image import EndImage
from commands.utility.decorators import fix_highlighted_player
import tracemalloc
from api.ddragon import get_latest_ddragon
from api.ddragon import get_champion_dict
from api.merakia import get_role_playrate_for_each_champ_id
from src.commands.utility.types import *

# from commands.utility.get_roles import get_roles
class ParseActiveGameData(Exception): pass

        
class loops(commands.Cog):
    def __init__(self, bot: commands.Bot, main_db: MainDB, betting_db: BettingDB, 
                 stalking_db: StalkingDB, riot_api: riotAPI, channel_id: int, ping_role_id: int, ddrag_version: str) -> None:
        self.bot = bot
        self.main_db = main_db
        self.betting_db = betting_db
        self.stalking_db = stalking_db
        self.riot_api = riot_api
        self.channel_id = channel_id
        self.ping_role_id = ping_role_id
        self.active_message_id = 0
        self.ddrag_version = ddrag_version 
        # Fix the db if there is a highlighted player
        fix_highlighted_player(self.main_db, self.betting_db, self.stalking_db)



    @tasks.loop(hours=24)
    async def refresh_ddrag(self):
        self.ddrag_version = await get_latest_ddragon()

    @commands.Cog.listener()
    async def on_ready(self):
        self.tracemalloc_started = False
        
        # Start tracing memory usage
        tracemalloc.start()
        self.tracemalloc_started = True
        print("Tracemalloc started in cog initialization.")
        self.activate_stalking.start()
        self.end_stalking.start()


    async def parse_active_game_data(self, active_game_info) -> ActiveGameData:
            """
                Parsing the data to my BaseModel, this could be done within the model
                but for readability sake i like to do it here
            """
            try:
                game_mode_mapping = {
                    0: "Custom",
                    400: "Normal",
                    420: "Ranked Solo/Duo",
                    430: "Blind Pick",
                    440: "Ranked Flex",
                    450: "ARAM",
                    700: "Clash"
                }
                teams_dict: Dict[int, List[Player]] = {100: [], 200: []}
                for participant in active_game_info['participants']:
                    game_name = participant['riotId'].lower().split('#')[0]

                    player = Player(
                        summoner_name=game_name,
                        champion_id=participant['championId'],
                        role= participant['role']
                    )
                    teams_dict[participant['teamId']].append(player)
                team_model = [Team(
                                team_id=team_id,
                                players=players) 
                                for team_id, players in teams_dict.items()]
                
                active_game_data = ActiveGameData(
                                        game_length=active_game_info['gameLength'],
                                        game_type=game_mode_mapping[active_game_info['gameQueueConfigId']],
                                        game_id=active_game_info['gameId'],
                                        teams=team_model
                                        )
            except Exception as e:
                raise ParseActiveGameData(f"Failed to parse active game data: {e}")
            return active_game_data

    @tasks.loop(minutes=2.0)
    async def activate_stalking(self):
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        try:
            if self.stalking_db.get_active_user():   
                return # if someone is being tracked
            possible_victims = self.stalking_db.get_all_users()
            print(f"Stalking victims of length: {len(possible_victims)}")
            victim = None
            for pos_victim in possible_victims:
                try:
                    # Small 1 second delay to not spam the requests
                    print(f"Checking if {pos_victim} is in game")
                    game_name, tag_line = pos_victim.split('#')
                    await asyncio.sleep(1)
                    # active, data, game_length, game_type = await self.riot_api.get_active_game_status(game_name, tag_line, self.ddrag_version)
                    active_game_info = await self.riot_api.get_active_game_status(game_name, tag_line, self.ddrag_version)
                    game_track_data: ActiveGameData = self.parse_active_game_data(active_game_info)
                except aiohttp.ClientResponseError as e:
                    continue

                # If game was already highlighted, dont show it again and look for another active game
                # or if game is too far gone or isnt ranked dont track
                if game_track_data.game_length > 600 or game_track_data.game_id != 420 or self.stalking_db.current_game == game_track_data.game_id:
                    print(f"Continuing, gametype {game_track_data.game_id}, gamelength {game_track_data.game_length} incorrect or game_id already being tracked")
                    continue
                victim = pos_victim
                break
            if not victim:
                print("No victims we")
                return
            message = None
            embed = None
            async with channel.typing():
                ## TODO: man really use a better datas structure here
                embed = discord.Embed(title=f":eyes::eyes:  {victim.upper()} IS IN GAME :eyes::eyes:\n"
                                            "YOU HAVE 10 MINUTES TO PREDICT!!!\n\n",
                                      description="HE WILL SURELY WIN, RIGHT?",
                                      color=0xFF0000)
                try:
                    image_creator: imageCreator = imageCreator(game_track_data, self.ddrag_version)
                    img = await image_creator.get_team_image()
                except aiohttp.ClientResponseError as e:
                    print("Failed to get images for image creator with exception: ", e)
                    return
                picture = discord.File(fp=img, filename="team.png")
                embed.set_image(url="attachment://team.png")

                if channel is not None:
                    try:
                        message = await channel.send(f"<@&{self.ping_role_id}>", file=picture, embed=embed)
                        self.betting_db.enable_betting()
                        print("Message sent successfully.")
                    except Exception as e:
                        print(e)
                        return
            self.stalking_db.current_game = data[0]
            # Only when there is no custom game we lock the highlighted player
            # Otherwise, we just show the game screen and continue with our lives
            self.stalking_db.change_status(victim, True)
            self.active_message_id = message.id
            await asyncio.sleep(self.betting_db.betting_time)
            # Send betting is no longer available
            try:
                embed_bet = discord.Embed(title="Betting is no longer enabled",
                                      color=0xFF0000)
                await channel.send(embed=embed_bet)
            except Exception as e:
                print(f"Betting no longer enabled message failed: {e}")
            async with channel.typing():
                all_bets = self.betting_db.get_all_bets()
                for decision in all_bets.keys():
                    text = ""
                    for discord_user in all_bets[decision]:
                        text += f"{discord_user['name']} **{discord_user['amount']}**\n"
                    embed.add_field(name=f"**{decision.upper()}**", value=text, inline=True)
                    if decision == "believers":
                        embed.add_field(name='\u200b', value='\u200b')
                try:
                    # embed.set_footer(text="Made by Matthijs (Aftershock)")
                    await message.edit(embed=embed)
                    print("Starting message updated.")
                except Exception as e:
                    print(f"Failed to update message: {e}")
        # Send the error in Discord
        except Exception as e:
            try:
                #await channel.send(f"Activate stalking error: {e}")
                print(f"Activate stalking error: {e}")
            except Exception as e:
                print(f"Activate stalking error: {e}")
        finally:
            # Take a memory snapshot
            pass
            # snapshot = tracemalloc.take_snapshot()
            # top_stats = snapshot.statistics("lineno")
            # print("[Top 10 Memory Stats]")
            # for stat in top_stats[:10]:
            #     print(stat)
                
                
    @tasks.loop(minutes=2.0)
    async def end_stalking(self):
        print("End stalking")
        channel_id: int = self.channel_id
        channel = self.bot.get_channel(channel_id)
        try:
            victim = self.stalking_db.get_active_user()
            ##
            victim = "1738#EUW" ##TODO:
            print(f"Active victim: {victim}")
            if victim is None:
                return
            
            match_id = f'EUW1_{self.stalking_db.current_game}'
            match_id = "EUW1_7223658854" ##TODO:
            try:
                match_data = await self.riot_api.get_full_match_details_by_matchID(match_id)
            except aiohttp.ClientResponseError:
                print("Game is still in progress")
                return
            try:
                endIm = EndImage(match_data, victim)
                end_image = await endIm.get_team_image(self.ddrag_version)
                end_result = endIm.get_game_result()
                picture = discord.File(fp=end_image, filename="team.png")
            except Exception as e:
                print(f"error in image: {e}")  
                return
            self.stalking_db.change_status(victim, False)
            self.betting_db.disable_betting()
            if end_result:
                description = "**WINNER WINNER CHICKEN DINNER 👑**\n"
                winners = "believers"
            else:
                description = "**BRO HAD NO IMPACT 🔥🔥**\n"
                winners = "doubters"

            #message: discord.Message = await channel.fetch_message(self.active_message_id) #TODO
            embed = discord.Embed(title=f"{victim.upper()}'S GAME RESULT IS IN :eyes::eyes:\n\n",
                                  description=description,
                                  color=0xFF0000)
            embed.set_image(url="attachment://team.png")
            all_bets = self.betting_db.get_all_bets()
            for decision in all_bets.keys():
                text = ""
                decide = "won" if decision == winners else "lost"
                for user in all_bets[decision]:
                    if decision == winners:
                        self.main_db.increment_field(user['discord_id'], "points", 2*int(user['amount']))
                    if decide == "won":
                        text += f"{user['name']} has {decide} {2*int(user['amount'])} points\n"
                    else:
                        text += f"{user['name']} has {decide} {user['amount']} points\n"
                embed.add_field(name=f"**{decision.upper()}**", value=text, inline=True)
                if decision == "believers":
                    embed.add_field(name='\u200b', value='\u200b')
            if channel is not None:
                try:
                    self.betting_db.remove_all_bets()
                    await channel.send(embed=embed, file=picture) #reference=message, 
                    print("Message sent successfully.")
                except discord.Forbidden:
                    print("I don't have permission to send messages to that channel.")
                except discord.HTTPException:
                    print("Failed to send the message.")
        # Send the error in Discord
        except Exception as e:
            try:
                await channel.send(f"End stalking error: {e}")
                print(f"End stalking error: {e}")
            except Exception as e:
                print(f"End stalking error: {e}")
        finally:
            # Take a memory snapshot
            pass
            # snapshot = tracemalloc.take_snapshot()
            # top_stats = snapshot.statistics("lineno")
            # print("[Top 10 Memory Stats]")
            # for stat in top_stats[:10]:
            #     print(stat)

async def setup(bot: commands.Bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    betting_db = BettingDB(settings.REDISURL)
    stalking_db = StalkingDB(settings.REDISURL)
    riot: riotAPI = riotAPI(settings.RIOTTOKEN)
    ddrag_version = await get_latest_ddragon()
    print("adding gametracker..")
    await bot.add_cog(loops(bot, main_db, betting_db, stalking_db, riot, settings.LIVEGAMECHANNELID, settings.PINGROLE, ddrag_version=ddrag_version))
