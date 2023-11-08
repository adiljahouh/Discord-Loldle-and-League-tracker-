from discord.ext import commands
from config import Settings
import discord
import random
import datetime
from commands.utility.decorators import role_check, super_user_check
from api.ddragon import get_champion_ddrag_format_list
from commands.utility.get_closest_word import find_closest_name
from databases.betting import BettingDB
from databases.main import MainDB
import pytz
import asyncio
from api.fandom import get_loldle_data

class PointCommands(commands.Cog):
    def __init__(self, main_db, betting_db, g_role, bot, cashoutchannelid) -> None:
        self.main_db: MainDB = main_db
        self.betting_db = betting_db
        self.g_role = g_role
        self.bot : commands.bot.Bot = bot
        self.cashoutCID = cashoutchannelid

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command()
    @super_user_check
    async def give(self, ctx, _, amount):
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
        """ Get daily points (500)"""
        async with ctx.typing():
            try:
                amsterdam_tz = pytz.timezone('Europe/Amsterdam')
                today = datetime.datetime.now(amsterdam_tz).date()
                userid = str(ctx.author.id)
                last_claim = self.main_db.get_user_field(discord_id=userid, field="last_claim")
                if last_claim is None or last_claim.decode('utf-8') != str(today.strftime('%Y-%m-%d')):
                    status = "You claim some points"
                    self.main_db.set_user_field(userid, "last_claim", today.strftime('%Y-%m-%d'))
                    self.main_db.increment_field(userid, "points", 500)
                else:
                    status = "You already claimed your points for today"
                points_bytes = self.main_db.get_user_field(userid, "points")
            except Exception as e:
                await ctx.send(e)
                return
            points = points_bytes.decode('utf-8')
            message = f'Total points: {points}'
            embed = discord.Embed(title=f"{status}\n\n",
                                  description=f"{message}",
                                  color=0xFF0000)
            await ctx.send(embed=embed)
    def compare_dicts_and_create_text(self, dict1, dict2)-> tuple:
        cross_emoji = "❌"
        check_emoji = "✅"
        result_text = ""
        
        # Initialize a flag to track if all values match
        all_values_match = True

        # Compare the dictionaries
        for key in dict1:
            if key in dict2:
                if isinstance(dict1[key], list) and isinstance(dict2[key], list):
                    # Both values are lists, compare items
                    matching_items = [f"{check_emoji} {item}" for item in dict1[key] if item in dict2[key]]
                    non_matching_items = [f"{cross_emoji} {item}" for item in dict1[key] if item not in dict2[key]]
                    if non_matching_items:
                        all_values_match = False  # Set flag to False if there are non-matching items
                    items_str = ' '.join(matching_items + non_matching_items)
                    result_text += f"{key}: {items_str}\n"
                elif dict1[key] == dict2[key]:
                    # Values match
                    result_text += f"{key}: {check_emoji} {dict1[key]}\n"
                else:
                    # Values don't match
                    result_text += f"{key}: {cross_emoji} {dict1[key]}\n"
                    all_values_match = False
            else:
                # Key doesn't exist in the second dictionary
                result_text += f"{key}: {cross_emoji} {dict1[key]} -> Key not found\n"
                all_values_match = False

        # Check for any extra keys in the second dictionary
        for key in dict2:
            if key not in dict1:
                # Key doesn't exist in the first dictionary
                result_text += f"{key}: {cross_emoji} Key not found -> {dict2[key]}\n"
                all_values_match = False

        # Return both the match flag and the result text
        return (all_values_match, result_text.strip())

    @commands.command()
    @role_check
    async def loldle(self, ctx, option="classic"):
        if option.lower() not in ["classic", "ability", "quote"]:
            await ctx.send("Invalid option, use .loldle <classic/ability/quote>")
            return
        try:
            amsterdam_tz = pytz.timezone('Europe/Amsterdam')
            today = datetime.datetime.now(amsterdam_tz).date()
            userid = str(ctx.author.id)
            last_claim = self.main_db.get_user_field(discord_id=userid, field="last_loldle")
            ##
            if last_claim is None or last_claim.decode('utf-8') != str(today.strftime('%Y-%m-%d')):
                status = f"Guess a champion and win 2000 points, for each guess wrong you lose 200 points. Not replying for over 90 seconds will close the game.\n\nStart the game by guessing a champ <@{userid}>."
                winning_guess_info = await get_loldle_data()
                ddragon_list = await get_champion_ddrag_format_list()
                # await ctx.send(winning_guess_info)

                correct_guess = False
                attempts = 0
                max_attempts = 10  # Set the maximum number of attempts here

                await ctx.send(status)
                # start LODLE api call and wait for response
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                
                while not correct_guess and attempts < max_attempts:
                    attempts += 1
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=90.0)
                        champion_guess = (msg.content.replace(" ", "")).capitalize()
                        score_and_ddrag_name = find_closest_name(champion_guess, ddragon_list)
                        ddrag_name = score_and_ddrag_name[0]
                        # await ctx.send(f"Your guess has been converted to {ddrag_name}")
                        try:
                            champion_guess_info = await get_loldle_data(ddrag_name)
                            # await ctx.send(champion_guess_info)
                            is_match_and_text = self.compare_dicts_and_create_text(champion_guess_info, winning_guess_info)
                            mention_and_text = is_match_and_text[1] + f"\n<@{userid}>"
                            await ctx.send(mention_and_text)
                            if is_match_and_text[0]:
                                correct_guess = True
                        except Exception as e:
                            await ctx.send(e)
                    except asyncio.TimeoutError:
                        await ctx.send(f'You took too long to respond, the champion was {winning_guess_info["Name"]}... Your game ended <@{userid}>.')
                        self.main_db.set_user_field(userid, "last_loldle", today.strftime('%Y-%m-%d'))
                        return
                if correct_guess:
                    points = 2000 - (attempts-1)*200
                    result = f"Correct guess! You earned {points} points <@{userid}>"
                else:
                    points = 0
                    result = f"Incorrect, the champion was {winning_guess_info['Name']}. You earned {points} points <@{userid}>"
                self.main_db.increment_field(userid, "points", points)
                self.main_db.set_user_field(userid, "last_loldle", today.strftime('%Y-%m-%d'))
            else:
                result = f"You already played a LOLDLE today <@{userid}>"
            total_points = self.main_db.get_user_field(userid, "points")
            await ctx.send(f"{result}, total points {total_points.decode()}")
        except Exception as e:
            await ctx.send(e)
            return
    @commands.command()
    @role_check
    async def cashout(self, ctx, option=""):
        async with ctx.typing():
            userid = str(ctx.author.id)
            total_points = self.main_db.get_user_field(userid, "points")
            cashout_options = {
                    "1000": "Buy a loldle",
                    "100000": "Change someones discord name for a day",
                    "150000": "Custom soundboard for a day",
                    "300000": "Pick anyone with the Player role's next champ",
                    "400000": "Backseat game 1 game of anyone with the Player Role",
                    "500000": "Time someone out for a day",
                    "1000000": "DUO GAME WITH MENNO "
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
                print(cost)
                print(int(total_points.decode()))
                if int(total_points.decode()) >= int(cost):
                    print("yes")
                    self.main_db.set_user_field(userid, "last_loldle", "2017-03-01")
                    self.main_db.decrement_field(discord_id=userid, field="points", amount=int(cost))
                else:
                    await ctx.send("not enough points to buy a loldle")
                    return
                await ctx.send(f"You are able to play a lodle again <@{userid}>, total points {total_points.decode()}")
                pass
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
                        await ctx.send("Pick a valid number")
                        return
                else:
                    await ctx.send("Please pick a reward")

    
    @commands.command()
    @role_check
    async def roll(self, ctx, *args):
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
    async def bet(self, ctx, *args):
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
            await ctx.send("Specify a whole number between 0-5000")
            return
        if amount <= 0 or amount > 5000:
            await ctx.send("Specify a whole number between 0-5000")
            return
        try:
            state = self.betting_db.store_bet(str(ctx.author.id), str(ctx.author.display_name), decision, amount)
            if state:
                embed = discord.Embed(title=f"{str(ctx.author.display_name)} has bet {amount} points on {decision}",
                                      color=0xFF0000)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Bet amount > point")
        except Exception as e:
            print(e)

    @commands.command()
    @role_check
    async def points(self, ctx):
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
    async def leaderboard(self, ctx, *args):
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
            embed.add_field(name="Top 10 point havers on the server", value=leaderboard_text)
            await ctx.send(embed=embed)
        except Exception as ex:
            print(ex)
            await ctx.send(ex)

    @commands.command()
    @role_check
    async def transfer(self, ctx, *args):
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


async def setup(bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    betting_db = BettingDB(settings.REDISURL)
    print("adding commands...")
    await bot.add_cog(PointCommands(main_db, betting_db, settings.GROLE, bot, settings.CASHOUTCHANNELID))
