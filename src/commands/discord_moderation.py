
from typing import Optional
from discord.ext import commands
from config import Settings
import discord
from commands.utility.decorators import role_check, mod_check, super_user_check
from databases.main import MainDB
class haterFanboyView(discord.ui.View):
    def __init__(self, *, timeout, hater, fanboy, botenthusiast, lunchers, leaguersid):
        super().__init__(timeout=timeout)
        self.fanboy_id = fanboy
        self.hater_id = hater
        self.botenthusiast_id = botenthusiast
        self.lunchers_id = lunchers
        self.leaguers_id = leaguersid
    
    async def add_role(self, interaction: discord.Interaction, button: discord.ui.Button, role_id: int, label: str, color: discord.ButtonStyle):
        user = interaction.user
        has_target_role = any(role.id == role_id for role in user.roles)
        if has_target_role:
            target_role = interaction.guild.get_role(role_id)
            await interaction.response.send_message(f"You already have the role {target_role.mention}", ephemeral=True)
        else:
            target_role = interaction.guild.get_role(role_id)
            if target_role:
                await user.add_roles(target_role)
                await interaction.response.send_message(f"You have been assigned the role {target_role.mention}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Role not found. {target_role.mention}", ephemeral=True)

    @discord.ui.button(label="FANBOY", style=discord.ButtonStyle.green)
    async def add_fanboy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_role(interaction, button, self.fanboy_id, "FANBOY", discord.ButtonStyle.green)

    @discord.ui.button(label="HATER", style=discord.ButtonStyle.red)
    async def add_hater(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_role(interaction, button, self.hater_id, "HATER", discord.ButtonStyle.red)

    @discord.ui.button(label="BOT ENTHUSIAST", style=discord.ButtonStyle.blurple, emoji="🤓")
    async def add_enthusiast(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_role(interaction, button, self.botenthusiast_id, "BOT ENTHUSIAST", discord.ButtonStyle.blurple)    

    @discord.ui.button(label="LUNCHERS", style=discord.ButtonStyle.primary, emoji="😋")
    async def add_lunchers(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_role(interaction, button, self.lunchers_id, "LUNCHERS", discord.ButtonStyle.primary)

    @discord.ui.button(label="LEAGUERS", style=discord.ButtonStyle.primary, emoji="🎮")
    async def add_leaguers(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_role(interaction, button, self.leaguers_id, "LEAGUERS", discord.ButtonStyle.primary)


class discMod(commands.Cog):
    def __init__(self, main_db, jail_role_id, confessional, bot, fanboyid, haterid, rolechannelid, main_channelid, botenthusiast, lunchers, leaguersid) -> None:
        self.bot: commands.bot.Bot = bot
        self.main_db = main_db
        self.jail_role = jail_role_id
        self.confessional = confessional
        self.fanboyroleid = fanboyid
        self.haterroleid = haterid
        self.rolechannelid = rolechannelid
        self.main_channelid = main_channelid
        self.botenthusiast_id = botenthusiast
        self.lunchers_id = lunchers
        self.leaguers_id = leaguersid
        self.jailed_users = {} #doing this with in-memory because not a lot will be jailed anyways

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(self.rolechannelid)

        if channel:
            await channel.purge()
            view = haterFanboyView(timeout=None, hater=self.haterroleid, fanboy=self.fanboyroleid, 
                                   botenthusiast=self.botenthusiast_id, lunchers=self.lunchers_id,
                                   leaguersid = self.leaguers_id)
            embed = discord.Embed(
            title="Choose Your Role",
            description="Click one of the buttons below to choose your role,\nbe sure to .register <league_name> to unlock all channels.",
            color=discord.Color.blue()
                )
            channel = self.bot.get_channel(self.rolechannelid)
            await channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Your on_member_join logic here...
        
        await member.send(f"Hi, {member.mention}!\n\n" \
                     f"To view the rest of the Discord, you need to register in <#{self.main_channelid}> using the following command:\n" \
                     f"```.register <riotname#tag>```\n" \
                     f"For example, a very sexy jungler would use: ```.register Mocro#zpr```\n\n" \
                     f"If you have already registered before this update, try re-registering to get access to all channels using the same command. If you encounter an error, it's possible that the League of Legends name is incorrect (you can try with a smurf account).\n\n" \
                     f"Please check out the <#{self.rolechannelid}> channel to pick a role after registering.")

    @commands.command()
    @role_check
    @mod_check
    async def release(self, ctx, member: discord.Member):
        """Release a user from jail."""
        jail_role = ctx.guild.get_role(self.jail_role)
        # Check if the member has the jail role
        if jail_role in member.roles:
            # Remove jail role
            await member.remove_roles(jail_role)

            # Add back the roles that were removed when the member was jailed
            if self.jailed_users[member.name]:
                for role in self.jailed_users[member.name]:
                    try:
                        await member.add_roles(role)
                    except Exception as e:
                        print(e)
                # Clear the removed roles from the database

            await ctx.send(f"<@{member.id}> has been released from jail.")
        else:
            await ctx.send(f"<@{member.id}> is not in jail.")

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
                            self.jailed_users[user.name] = user.roles
                            for current_role in user.roles:
                                if current_role.name == "@everyone":
                                    continue
                                try:
                                    await user.remove_roles(current_role)
                                except discord.Forbidden:
                                    print(f"Skipped a role I could not remove: {current_role.name}")
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
                            embed = discord.Embed(title=f"You <@{mention.id}> have been jailed for the following violations\n\n",
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
    await bot.add_cog(discMod(main_db, settings.JAILROLE, settings.CONFESSIONALCHANNELID, bot, 
                              settings.FANBOYROLEID, settings.HATERROLEID, settings.ROLECHANNELID, 
                              settings.CHANNELID, settings.PINGROLE, settings.LUNCHERS,
                              settings.LEAGUERSID))