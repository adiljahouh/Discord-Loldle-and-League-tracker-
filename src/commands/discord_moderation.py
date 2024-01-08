
from typing import Optional
from discord.ext import commands
from config import Settings
import discord
from commands.utility.decorators import role_check, mod_check, super_user_check
from databases.main import MainDB
from discord.ui import View, Button
class haterFanboyView(discord.ui.View):
    def __init__(self, *, timeout, hater, fanboy):
        super().__init__(timeout=timeout)
        self.fanboy_id = fanboy
        self.hater_id = hater
    
    
    @discord.ui.button(label="FANBOY", 
                       style=discord.ButtonStyle.green)
    async def add_fanboy(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        has_target_role = any(role.id == self.fanboy_id for role in user.roles)
        if has_target_role:
            print("dong")
            target_role = interaction.guild.get_role(self.fanboy_id)
            await interaction.response.send_message(f"You already have the role {target_role.mention}", ephemeral=True)
        else:
            print("DING")
            # Add the role if the user doesn't have it
            target_role = interaction.guild.get_role(self.fanboy_id)
            if target_role:
                await user.add_roles(target_role)
                await interaction.response.send_message(f"You have been assigned the role {target_role.mention}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Role not found. {target_role.mention}", ephemeral=True)
        
    @discord.ui.button(label="HATER", 
                       style=discord.ButtonStyle.red)
    async def add_hater(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        has_target_role = any(role.id == self.hater_id for role in user.roles)
        if has_target_role:
            print("dong")
            target_role = interaction.guild.get_role(self.hater_id)
            await interaction.response.send_message(f"You already have the role {target_role.mention}", ephemeral=True)
        else:
            print("DING")
            # Add the role if the user doesn't have it
            target_role = interaction.guild.get_role(self.hater_id)
            if target_role:
                await user.add_roles(target_role)
                await interaction.response.send_message(f"You have been assigned the role {target_role.mention}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Role not found. {target_role.mention}", ephemeral=True)
        


class discMod(commands.Cog):
    def __init__(self, main_db, jail_role_id, confessional, bot, fanboyid, haterid, rolechannelid, main_channelid) -> None:
        self.bot: commands.bot.Bot = bot
        self.main_db = main_db
        self.jail_role = jail_role_id
        self.confessional = confessional
        self.fanboyroleid = fanboyid
        self.haterroleid = haterid
        self.rolechannelid = rolechannelid
        self.main_channelid = main_channelid

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(self.rolechannelid)

        if channel:
            await channel.purge()
            view = haterFanboyView(timeout=None, hater=self.haterroleid, fanboy=self.fanboyroleid)
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
    await bot.add_cog(discMod(main_db, settings.JAILROLE, settings.CONFESSIONALCHANNELID, bot, 
                              settings.FANBOYROLEID, settings.HATERROLEID, settings.ROLECHANNELID, settings.CHANNELID))