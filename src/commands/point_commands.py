from discord.ext import commands
from config import Settings
import discord
import random
import datetime
from commands_utility import role_check
from main_db import MainDB
from betting_db import BettingDB


class PointCommands(commands.Cog):
    def __init__(self, main_db, betting_db, g_role) -> None:
        self.main_db = main_db
        self.betting_db = betting_db
        self.g_role = g_role

    @commands.Cog.listener()
    async def on_ready(self):
        pass

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
            await ctx.send("Specify an integer amount larger than 0")
            return
        if amount <= 0:
            await ctx.send("Specify an integer amount larger than 0")
            return
        try:
            state = self.betting_db.store_bet(str(ctx.author.id), str(ctx.author.name), decision, amount)
            if state:
                embed = discord.Embed(title=f"{str(ctx.author.name)} has bet {amount} points on {decision}",
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


async def setup(bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    betting_db = BettingDB(settings.REDISURL)
    print("adding commands...")
    await bot.add_cog(PointCommands(main_db, betting_db, settings.GROLE))
