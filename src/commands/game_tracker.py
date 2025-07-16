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
from api.ddragon import get_latest_ddragon, get_champion_dict
from api.merakia import get_role_playrate_for_each_champ_id
import traceback
from commands.utility.types import *
from commands.utility.get_roles import order_team
class ParseActiveGameData(Exception): pass
class NoValidVictimFound(Exception): pass
class MessageSendError(Exception): pass
class UpdateBettingResultsMessageError(Exception): pass
        
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
        self.all_champions = None # set in on_ready
        self.champion_all_roles_playrate = None # set in on_ready
        # Fix the db if there is a highlighted player
        fix_highlighted_player(self.main_db, self.betting_db, self.stalking_db)



    @tasks.loop(hours=24)
    async def refresh_ddrag(self):
        self.ddrag_version = await get_latest_ddragon()

    @commands.Cog.listener()
    async def on_ready(self):
        self.all_champions = await get_champion_dict(self.ddrag_version)
        # dict of champion_id: {role: playrate}
        self.champion_all_roles_playrate = await get_role_playrate_for_each_champ_id()
        self.activate_stalking.start()
        self.end_stalking.start()

    async def send_betting_message(self, channel: discord.TextChannel, victim: str, game_data: ActiveGameData) -> discord.Message:
        try:
            image_creator = imageCreator(game_data, self.ddrag_version)
            print(f"Creating team image for {victim}...")
            img = await image_creator.get_team_image()
            print(img)
            picture = discord.File(fp=img, filename="team.png")

            embed = discord.Embed(
                title=f":eyes::eyes:  {victim.upper()} IS IN GAME :eyes::eyes:\n\nYOU HAVE 10 MINUTES TO PREDICT!!!",
                description="HE WILL SURELY WIN, RIGHT?",
                color=0xFF0000
            )
            embed.set_image(url="attachment://team.png")

            return await channel.send(f"<@&{self.ping_role_id}>", file=picture, embed=embed)
        except aiohttp.ClientResponseError as e:
            raise MessageSendError(f"Image creation or send failed: {type(e).__name__}: {e}")
        except discord.HTTPException as e:
            raise MessageSendError(f"Discord send failed: {type(e).__name__}: {e}")
        
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
                        champ_name=self.all_champions[str(participant['championId'])]
                        )

                    teams_dict[participant['teamId']].append(player)
                team_model = [Team(
                                team_id=team_id,
                                players=players) 
                                for team_id, players in teams_dict.items()]
                team_model = order_team(self.champion_all_roles_playrate, team_model)
                #print(f"Ordered teams: {team_model}")
                active_game_data = ActiveGameData(
                                        game_length=active_game_info['gameLength'],
                                        game_type=game_mode_mapping[active_game_info['gameQueueConfigId']],
                                        game_id=active_game_info['gameId'],
                                        teams=team_model
                                        )
            except Exception as e:
                print(traceback.format_exc())
                raise ParseActiveGameData(f"Failed to parse active game data: {type(e).__name__}: {e}")
            return active_game_data
    
    async def find_valid_victim(self) -> tuple[str, ActiveGameData]:
        for victim_riotid_and_tag in self.stalking_db.get_all_users():
            try:
                game_name, tag_line = victim_riotid_and_tag.split('#')
                await asyncio.sleep(1)
                print(f"Checking {game_name}#{tag_line} for active game...")
                raw_active_game_info = await self.riot_api.get_active_game_status(game_name, tag_line, self.ddrag_version)
                game_track_data = await self.parse_active_game_data(raw_active_game_info)
                if game_track_data.game_length > 60000 or game_track_data.game_type != 'Ranked Solo/Duo' or self.stalking_db.current_game == game_track_data.game_id:
                    print(f"Skipping {victim_riotid_and_tag} - game too long, not ranked, or already being tracked.")
                    continue  # Skip if game is too long, not ranked, or already being tracked

                return victim_riotid_and_tag, game_track_data

            except (aiohttp.ClientResponseError, ParseActiveGameData):
                continue  # just skip this victim

        raise NoValidVictimFound("No valid victims found (not in game).")
    
    async def update_betting_results_message(self, message: discord.Message):
        try:
            embed = message.embeds[0]  # use the existing embed
            all_bets = self.betting_db.get_all_bets()

            for decision, users in all_bets.items():
                text = "\n".join(f"{user['name']} **{user['amount']}**" for user in users)
                embed.add_field(name=f"**{decision.upper()}**", value=text, inline=True)

                # Add spacing between columns
                if decision == "believers":
                    embed.add_field(name='\u200b', value='\u200b')

            await message.edit(embed=embed)
            print("Message updated with bets.")
        except Exception as e:
            raise UpdateBettingResultsMessageError(f"Failed to update betting results message: {type(e).__name__}: {e}") 

    @tasks.loop(minutes=2.0)
    async def activate_stalking(self):
        channel: discord.TextChannel = self.bot.get_channel(self.channel_id)
        if not channel:
            print("Channel not found.")
            return
        if self.stalking_db.get_active_user():   
            return # if someone is being tracked
        try:
            victim, game_data = await self.find_valid_victim()
        except (NoValidVictimFound, aiohttp.ClientResponseError, ParseActiveGameData) as e:
            print(f"{type(e).__name__}: {e}")
            # print(traceback.format_exc())
            return
        # Send initial betting image and message
        try:
            async with channel.typing():
                message = await self.send_betting_message(channel, victim, game_data)
        except MessageSendError as e:
            print(traceback.format_exc())
            print(f"Failed to send betting message: {type(e).__name__}: {e}")
            return

        self.betting_db.enable_betting()
        self.stalking_db.current_game = game_data.game_id
        self.stalking_db.change_status(victim, True)
        self.active_message_id = message.id

        # Wait for the betting time
        await asyncio.sleep(self.betting_db.betting_time)
        try:
            async with channel.typing():
                self.update_betting_results_message(message)
                await channel.send(embed=discord.Embed(title="Betting is no longer enabled", color=0xFF0000))
        except UpdateBettingResultsMessageError as e:
            # print(traceback.format_exc())
            print(f"Failed to update message with bets: {type(e).__name__}: {e}")
        except Exception as e:
            # print(traceback.format_exc())
            print(f"Failed to send 'betting disabled' message: {type(e).__name__}: {e}")         
                
    @tasks.loop(minutes=2.0)
    async def end_stalking(self):
        channel: discord.TextChannel = self.bot.get_channel(self.channel_id)
        try:
            victim = self.stalking_db.get_active_user()
            #victim = "1738#EUW" ##TODO:
            print(f"Active victim end stalker: {victim}")
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
                print(f"error in image:  {type(e).__name__}: {e}")  
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
            print(traceback.format_exc())
            print(f"End stalking error: {type(e).__name__}: {e}")

async def setup(bot: commands.Bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    betting_db = BettingDB(settings.REDISURL)
    stalking_db = StalkingDB(settings.REDISURL)
    riot: riotAPI = riotAPI(settings.RIOTTOKEN)
    ddrag_version = await get_latest_ddragon()
    print("adding gametracker..")
    await bot.add_cog(loops(bot, main_db, betting_db, stalking_db, riot, settings.LIVEGAMECHANNELID, settings.PINGROLE, ddrag_version=ddrag_version))
