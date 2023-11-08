import aiohttp
from discord.ext import commands
from config import Settings
import discord
import os
import uuid
from commands.utility.decorators import role_check, mod_check
from databases.main import MainDB
import asyncio


class discMod(commands.Cog):
    def __init__(self, main_db, jail_role_id, confessional, bot) -> None:
        self.bot: commands.bot.Bot = bot
        self.main_db = main_db
        self.jail_role = jail_role_id
        self.confessional = confessional

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.command()
    @role_check
    @mod_check
    async def strike(self, ctx, *args):
        """Strike someone by using .strike @<user> <reason>"""
        mentions = ctx.message.mentions
        if len(mentions) == 0:
            await ctx.send("Mention someone to strike e.g. .add strike <@319921436519038977> for being a BOTTOM G")
        else:
            for mention in mentions:
                filtered_args = [arg for arg in list(args) if str(mention.id) not in arg]
                if len(filtered_args) == 0:
                    # if we didnt pass a reason
                    filtered_args.append("No reason")
                if self.main_db.check_user_existence(mention.id) == 1:
                    total = self.main_db.increment_field(mention.id, "strikes", 1)
                    success = self.main_db.set_user_field(mention.id, f"strike_{total}", f"{' '.join(filtered_args)}")
                    if total >= 3:
                        success = self.main_db.set_user_field(mention.id, "strikes", 0)
                        if success == 0:
                            user = ctx.guild.get_member(mention.id)
                            for current_role in user.roles:
                                if current_role.name == "@everyone":
                                    continue
                                await user.remove_roles(current_role)
                            jail_role = ctx.guild.get_role(self.jail_role)
                            await ctx.send(f"YOU EARNED A STRIKE <@{mention.id}> BRINGING YOU TO {total} STRIKES WHICH MEANS YOU'RE OUT , WELCOME TO MAXIMUM SECURITY JAIL {jail_role.mention}")
                            strike_reasons = ""
                            for strike in range(1,4):
                                try:
                                    reason = self.main_db.get_user_field(mention.id, f"strike_{strike}")
                                    strike_reasons += f"Strike {strike}: {reason.decode('utf8')}\n"
                                except Exception as e:
                                    pass
                            await user.add_roles(jail_role)
                            channel= self.bot.get_channel(self.confessional)
                            embed = discord.Embed(title=f"You have been jailed for the following violations\n\n",
                                  description=f"{strike_reasons}",
                                  color=0xFF0000)
                            await channel.send(embed=embed)
                        else:
                            await ctx.send(f"Couldnt reset your strikes, contact an admin")
                    else:
                        await ctx.send(f"YOU EARNED A STRIKE <@{mention.id}> for {' '.join(filtered_args)}\n TOTAL COUNT: {total}")
                else:
                    await ctx.send(
                        f"You cannot strike <@{mention.id}> because (s)he has not registered yet, <@{mention.id}> please use .register <your_league_name>")


async def setup(bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    print("adding discord commands...")
    await bot.add_cog(discMod(main_db, settings.JAILROLE, settings.CONFESSIONALCHANNELID, bot))