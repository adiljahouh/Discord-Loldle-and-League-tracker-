from discord.ext import commands
from config import Settings
import discord
import random
import datetime
from commands.utility.decorators import role_check, super_user_check
from api.ddragon import get_champion_ddrag_format_list, get_latest_ddragon
from commands.utility.get_closest_word import find_closest_name
from commands.utility.loldle import *
from databases.betting import BettingDB
from databases.main import MainDB
from databases.loldle import loldleDB
import pytz
class PointCommands(commands.Cog):
    def __init__(self, main_db: MainDB, betting_db: BettingDB, g_role: int, bot: commands.Bot,
                  cashoutchannelid: int, loldle_db: loldleDB) -> None:
        self.main_db = main_db
        self.betting_db = betting_db
        self.g_role = g_role
        self.bot = bot
        self.cashoutCID = cashoutchannelid
        self.loldle_db = loldle_db


    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command()
    @super_user_check
    async def give(self, ctx, _, amount):
        """Give points to a user by .give @user <number>"""
        async with ctx.typing():
            try:
                mentions = ctx.message.mentions
                if len(mentions) == 0 or len(mentions) > 1:
                    await ctx.send("Mention 1 person to grant points")
                    return
                self.main_db.increment_field(mentions[0].id, "points", int(amount))
                points_bytes = self.main_db.get_user_field(mentions[0].id, "points")
            except Exception as e:
                await ctx.send(e)
                return
            points = points_bytes.decode('utf-8')
            message = f'Total points: {points}'
            embed = discord.Embed(title=f"{'You have been given some points'}\n\n",
                                  description=f"{message}",
                                  color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.command()
    @role_check
    async def daily(self, ctx):
        """ Get daily points (1000) and strikes (3) by using .daily """
        async with ctx.typing():
            try:
                amsterdam_tz = pytz.timezone('Europe/Amsterdam')
                today = datetime.datetime.now(amsterdam_tz).date()
                userid = str(ctx.author.id)
                last_claim = self.main_db.get_user_field(discord_id=userid, field="last_claim")
                if last_claim is None or last_claim.decode('utf-8') != str(today.strftime('%Y-%m-%d')):
                    status = "You claim some points"
                    self.main_db.set_user_field(userid, "last_claim", today.strftime('%Y-%m-%d'))
                    current_strikes_bytes = self.main_db.get_user_field(userid, "strike_quota")
                    current_strikes = current_strikes_bytes.decode('utf-8') if current_strikes_bytes else "0"
                    if int(current_strikes) < 3:
                        incr_by = 3 - int(current_strikes)
                        self.main_db.increment_field(userid, "strike_quota", incr_by)
                    self.main_db.increment_field(userid, "points", 1000)
                else:
                    status = "You already claimed your points and strikes for today"
                points_bytes = self.main_db.get_user_field(userid, "points")
                strikes_bytes = self.main_db.get_user_field(userid, "strike_quota")
            except Exception as e:
                await ctx.send(e)
                return
            points = points_bytes.decode('utf-8')
            strikes = strikes_bytes.decode('utf-8') if strikes_bytes else "0" 
            message = f'Total points: {points}\nTotal strikes: {strikes}'
            embed = discord.Embed(title=f"{status}\n\n",
                                  description=f"{message}",
                                  color=0xFF0000)
            await ctx.send(embed=embed)
    

    @commands.command()
    @role_check
    async def loldle(self, ctx: commands.Context):
        try:
            amsterdam_tz = pytz.timezone('Europe/Amsterdam')
            today = datetime.datetime.now(amsterdam_tz).date()
            userid = str(ctx.author.id)
            last_claim = self.main_db.get_user_field(discord_id=userid, field="last_loldle")
            ddrag_version = await get_latest_ddragon()
            if last_claim is None or last_claim.decode('utf-8') != str(today.strftime('%Y-%m-%d')):
                random_champ_name = self.loldle_db.get_random_champion_name() # by ddrag format
                champ_info: dict = self.loldle_db.get_champion_info(random_champ_name)
                all_champs = self.loldle_db.get_all_champ_keys() # concatenated keys e.g.  AurelionSol
                embed = discord.Embed(
                title="Pick a Loldle type",
                description="Points earned and attempts vary per game type below",
                color=discord.Color.blue()
                )
                print("Loldle started with winning guess, ", champ_info)
                view = loldleView(timeout=200, ctx=ctx, champ_list=all_champs, bot=self.bot, main_db=self.main_db, day=today,
                                  winning_guess_info=champ_info, loldle_db = self.loldle_db, ddrag_version=ddrag_version)
                await ctx.send(embed=embed, view=view)
            else:
                result = f"You already played a LOLDLE today <@{userid}> , use .cashout 1 to buy one"
                total_points = self.main_db.get_user_field(userid, "points")
                await ctx.send(f"{result}, total points {total_points.decode()}")  
        except Exception as e:
            print(e)

    @commands.command()
    @role_check
    async def cashout(self, ctx: commands.Context, option=""):
        """
            Buy rewards by using .cashout <number> or to view rewars use .cashout
        """
        async with ctx.typing():
            userid = str(ctx.author.id)
            total_points = self.main_db.get_user_field(userid, "points")
            cashout_options = {
                    "1000": "Buy a loldle",
                    "50000": "Buy a strike",
                    "150000": "Custom soundboard",
                    "250000": "Custom role",
                    "300000": "Pick anyone with the Player role's next champ (scrim)",
                    "400000": "Backseat a scrim",
                    "500000": "Time someone out for a day",
                    "600000": "Custom event",
                    "700000": "Join a scrim",
                    "800000": "Custom bot command",
                    "900000": "Change discord picture",
                    "1000000": "Join a turbo cool loch ness event/party"
                }
            if option=="":
                try:
                    numbered_list = "\n".join([f"{i+1}. {int(key):,} points -> {value}" for i, (key, value) in enumerate(cashout_options.items())])
                except Exception as e:
                    await ctx.send(e)
                embed = discord.Embed(title=f"💰 Rewards 💰\n\n",
                        description=f"{numbered_list}",
                        color=0xFF0000)
                await ctx.send(embed=embed)
                return
            elif option=="1":
                cost = [i for i in cashout_options.keys()][int(option)-1]
                if int(total_points.decode()) >= int(cost):
                    self.main_db.set_user_field(userid, "last_loldle", "2017-03-01")
                    self.main_db.decrement_field(discord_id=userid, field="points", amount=int(cost))
                else:
                    await ctx.send("not enough points to buy a loldle")
                    return
                new_points = self.main_db.get_user_field(userid, "points")
                await ctx.send(f"You are able to play a lodle again <@{userid}>, total points {new_points.decode()}")
                pass
            elif option == "2": # strike bought
                cost = [i for i in cashout_options.keys()][int(option)-1]
                if int(total_points.decode()) >= int(cost):
                    self.main_db.increment_field(userid, "strike_quota", 1)
                    new_points = self.main_db.decrement_field(discord_id=userid, field="points", amount=int(cost))
                    await ctx.send(f"<@{userid}> bought a strike, total points {new_points.decode()}")
                else:
                    await ctx.send(f"not enough points to buy a strike, total points {total_points.decode()}")
                    return
                
            else:
                if option.isdigit():
                    try:
                        channel = self.bot.get_channel(self.cashoutCID)
                        reward = [i for i in cashout_options.values()][int(option)-1]
                        cost = [i for i in cashout_options.keys()][int(option)-1]
                        if int(total_points.decode()) >= int(cost):
                            self.main_db.decrement_field(discord_id=userid, field="points", amount=int(cost))
                            await channel.send(f"<@{userid}> cashed out: {reward}")
                        else:
                            await ctx.send(f"You dont have enough points for this option, total points {total_points.decode()}")
                    except IndexError:
                        await ctx.send("Pick a valid number by using .cashout <number>")
                        return
                else:
                    await ctx.send("Please pick a reward by using .cashout <number>")

    
    @commands.command()
    @role_check
    async def roll(self, ctx: commands.Context, *args):
        """Roll your points by using .roll <points>"""
        async with ctx.typing():
            userid = str(ctx.author.id)
            points_bytes = self.main_db.get_user_field(userid, "points")
            if points_bytes is None:
                await ctx.send("You have no points,  type .daily to get your points")
                return
            if len(args) == 0:
                await ctx.send("Amount has to be specified .roll <amount>")
                return
            number = args[0]
            points = points_bytes.decode('utf-8')
            try:
                number = int(number)
            except ValueError:
                await ctx.send("Specify a valid amount larger than 0")
                return
            if number <= 0:
                await ctx.send("Specify a valid amount larger than 0")
                return
            if number > int(points):
                await ctx.send(f"You do not have enough points for this, total points: {points}")
                return
            roll = random.choice(['Heads', 'Tails'])
            if roll != 'Heads':
                try:
                    self.main_db.decrement_field(userid, "points", number)
                except Exception as e:
                    print(e)
                new_points = self.main_db.get_user_field(userid, "points")
                status = "LOLOLOLOLO-LOSER"
            else:
                self.main_db.increment_field(userid, "points", number)
                new_points = self.main_db.get_user_field(userid, "points")
                status = "You won!"
            embed = discord.Embed(title=f"{status}\n\n",
                                  description=f"Original points: {points}\nNew points: {new_points.decode('utf-8')}",
                                  color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.command()
    @role_check
    async def bet(self, ctx: commands.Context, *args):
        """
            Bet points with .bet <win/lose> <amount>
        """
        print("Bet command")
        if not self.betting_db.get_betting_state():
            await ctx.send("Betting not enabled")
            return
        if len(args) != 2 or args[0].lower() not in ["win", "lose"]:
            await ctx.send("Use .bet <win/lose> <amount>")
            return
        decision = "believers" if args[0] == "win" else "doubters"
        try:
            amount = int(args[1])
        except ValueError:
            await ctx.send("Specify a whole number between 0-10000")
            return
        if amount <= 0 or amount > 10000:
            await ctx.send("Specify a whole number between 0-10000")
            return
        try:
            state = self.betting_db.store_bet(str(ctx.author.id), str(ctx.author.display_name), decision, amount)
            if state == 1:
                embed = discord.Embed(title=f"{str(ctx.author.display_name)} has bet {amount} points on {decision}",
                                      color=0xFF0000)
                await ctx.send(embed=embed)
            elif state == 0:
                await ctx.send(f"Bet amount > point")
            elif state == 2:
                await ctx.send("You already bet on this game")
        except Exception as e:
            print(e)

    @commands.command()
    @role_check
    async def points(self, ctx: commands.Context):
        """
            Returns amount of points of the current user
        """
        print("Points command")
        points = self.main_db.get_user_field(str(ctx.author.id), "points")
        if points is None:
            points = 0
        else:
            points = points.decode('utf8')
        embed = discord.Embed(title=f"You have {points} points", color=0xFF0000)
        try:
            await ctx.send(embed=embed)
            print("Message sent successfully.")
        except discord.Forbidden:
            print("I don't have permission to send messages to that channel.")
        except discord.HTTPException:
            print("Failed to send the message.")

    @commands.command()
    @role_check
    async def leaderboard(self, ctx: commands.Context, *args):
        """
            Returns point leaderboard with pagination support
        """
        try:
            print("Leaderboard command")
            leaderboard = None
            page_number = 1
            page_size = 10
            if len(args) == 0:
                leaderboard = self.main_db.get_all_users_sorted_by_field("points", True, 0, page_size)
            else:
                try:
                    page_number = int(args[0])
                    if page_number <= 0:
                        await ctx.send("Specify a whole number larger than 0")
                        return
                    start = (page_number - 1) * page_size
                    leaderboard = self.main_db.get_all_users_sorted_by_field("points", True, start, page_size)
                except ValueError:
                    await ctx.send("Specify a whole number larger than 0")
                    return
            leaderboard_text = ''
            for index, user in enumerate(leaderboard):
                leaderboard_text += f'\n{index + 1 + ((page_number * 10) - 10)}. <@{user[0]}> | {user[1]} points'
            description = f"99 percent of gamblers quit right before they hit it big! \n This is page {page_number}, to look at the next page use '.leaderboard {page_number+1}'"
            embed = discord.Embed(title="Biggest gambling addicts 🃏\n\n", description=f"{description}", color=0xFF0000)
            #embed.set_footer(text="Made by Stephen (Smikkelen)")
            embed.add_field(name="Top 10 point havers on the server", value=leaderboard_text)
            await ctx.send(embed=embed)
        except Exception as ex:
            print(ex)
            await ctx.send(ex)

    @commands.command()
    @role_check
    async def transfer(self, ctx: commands.Context, *args):
        """
            Transfer your points to another player .transfer <@player> <points>
        """
        try:
            print(f"Transfer command: {args}")
            if len(args) != 2 or len(args[0]) < 3:
                await ctx.send("Use .transfer <@player> <points>")
                return
            discord_id = bytes(args[0][2:-1], 'utf-8')
            try:
                points = int(args[1])
            except ValueError:
                await ctx.send("Use .transfer <@player> <points>")
                return
            all_players = self.main_db.get_all_users()
            if discord_id not in all_players:
                await ctx.send("User is not registered")
                return
            if points <= 0:
                await ctx.send("Points must be larger than 0")
                return
            player_points = int(self.main_db.get_user_field(ctx.author.id, "points"))
            if player_points < points:
                await ctx.send("You do not have enough points")
                return
            self.main_db.decrement_field(ctx.author.id, "points", points)
            self.main_db.increment_field(discord_id, "points", points)
            embed = discord.Embed(title=f"Transferred {points} points", color=0xFF0000)
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
            await ctx.send(e)


async def setup(bot: commands.Bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    betting_db = BettingDB(settings.REDISURL)
    loldle_db = loldleDB(settings.REDISURL)
    print("adding commands...")
    await bot.add_cog(PointCommands(main_db=main_db, betting_db=betting_db, g_role=settings.GROLE, 
                                    bot=bot, cashoutchannelid=settings.CASHOUTCHANNELID, loldle_db=loldle_db))
