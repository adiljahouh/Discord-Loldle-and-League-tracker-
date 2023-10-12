from discord.ext import commands
from config import Settings
import discord
import random
import datetime
from commands.commands_utility import role_check, super_user_check
from databases.betting_db import BettingDB
from databases.main_db import MainDB

class PointCommands(commands.Cog):
    def __init__(self, main_db, betting_db, g_role) -> None:
        self.main_db = main_db
        self.betting_db = betting_db
        self.g_role = g_role

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
        async with ctx.typing():
            try:
                today = datetime.datetime.now().date()
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
            await ctx.send("Specify a whole number larger than 0")
            return
        if amount <= 0:
            await ctx.send("Specify a whole number larger than 0")
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
        print("Leaderboard command")
        leaderboard = None
        page_number = 1
        if len(args) == 0:
            leaderboard = self.main_db.get_all_users_sorted_by_field("points", True, 0, 9)
        else:
            try:
                if page_number <= 0:
                    await ctx.send("Specify a whole number larger than 0")
                    return
                page_size = 10
                start = (page_number - 1) * page_size
                end = start + page_size - 1
                leaderboard = self.main_db.get_all_users_sorted_by_field("points", True, start, end)
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

async def setup(bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    betting_db = BettingDB(settings.REDISURL)
    print("adding commands...")
    await bot.add_cog(PointCommands(main_db, betting_db, settings.GROLE))
