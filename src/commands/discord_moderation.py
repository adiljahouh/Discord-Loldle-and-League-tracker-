
from typing import Optional
from discord.ext import commands
from config import Settings
import discord
from commands.utility.decorators import role_check, mod_check, super_user_check
from databases.main import MainDB
from commands.utility.dead_or_alive import draw_dead_or_alive, get_profile_pic
from datetime import datetime, timezone
import asyncio
class haterFanboyView(discord.ui.View):
    def __init__(self, *, timeout, hater_id, fanboy_id, botenthusiast_id, lunchers_id, leaguers_id, variety_id):
        super().__init__(timeout=timeout)
        print("initializing")
        self.fanboy_id = fanboy_id
        self.hater_id = hater_id
        self.botenthusiast_id = botenthusiast_id
        self.lunchers_id = lunchers_id
        self.leaguers_id = leaguers_id
        self.variety_id = variety_id
    
    async def add_role(self, interaction: discord.Interaction, button: discord.ui.Button, role_id: int, label: str, color: discord.ButtonStyle):
        user = interaction.user
        has_target_role = any(role.id == role_id for role in user.roles)
        if has_target_role:
            target_role = interaction.guild.get_role(role_id)
            await user.remove_roles(target_role)
            await interaction.response.send_message(f"Removing the role {target_role.mention}", ephemeral=True)
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

    @discord.ui.button(label="VARIETY", style=discord.ButtonStyle.primary, emoji="🎲")
    async def add_variety(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_role(interaction, button, self.variety_id, "VARIETY", discord.ButtonStyle.primary)


class discMod(commands.Cog):
    def __init__(self, main_db, jail_role_id, confessional_channel_id, bot, fanboyid, haterid, rolechannelid, main_channelid,
                  botenthusiastid, lunchersid, leaguersid, varietyid) -> None:
        self.bot: commands.bot.Bot = bot
        self.main_db = main_db
        self.jail_role = jail_role_id
        self.confessional = confessional_channel_id
        self.fanboyroleid = fanboyid
        self.haterroleid = haterid
        self.rolechannelid = rolechannelid
        self.main_channelid = main_channelid
        self.botenthusiast_id = botenthusiastid
        self.lunchers_id = lunchersid
        self.leaguers_id = leaguersid
        self.variety_id = varietyid
        self.jailed_users = {} #doing this with in-memory because not a lot will be jailed anyways
        self.active_destruction_target = None

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(self.rolechannelid)

        if channel:
            await channel.purge()
            view = haterFanboyView(timeout=None, hater_id=self.haterroleid, fanboy_id=self.fanboyroleid, 
                                    botenthusiast_id=self.botenthusiast_id, lunchers_id=self.lunchers_id,
                                    leaguers_id = self.leaguers_id, variety_id=self.variety_id)
            embed = discord.Embed(
            title="Choose Your Role",
            description="Click one of the buttons below to choose your role,\nbe sure to .register <league_name> to unlock all channels.",
            color=discord.Color.blue()
                )
            channel = self.bot.get_channel(self.rolechannelid)
            print("sending roles to roole channel")
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
    async def release(self, ctx: commands.Context, member: discord.Member):
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
    async def strike(self, ctx: commands.Context, *args):
        """Strike someone by using .strike @<user> <reason>"""
        mentions = ctx.message.mentions
        attachments = ctx.message.attachments  # Get attachments
        attachment_urls = [attachment.url for attachment in attachments]
        # from the command text remove all @'s to filter out the reason
        strike_reasoning = [arg for arg in args if not any(str(mention.id) in arg for mention in mentions)]
        if len(strike_reasoning) == 0:
            # if no reason is provided
            strike_reasoning.append("No reason mentioned")


        if len(mentions) == 0:
            await ctx.send("Mention someone to strike e.g. .add strike <@319921436519038977> for being a BOTTOM G")
        else:
            for mention in mentions:
                # filtered_args = [arg for arg in list(args) if str(mention.id) not in arg]
                if self.main_db.check_user_existence(mention.id) == 1:
                    total = self.main_db.increment_field(mention.id, "strikes", 1)
                    
                    # Prepare reason and attachments string
                    reason = ' '.join(strike_reasoning)
                    attachments_str = ', '.join(attachment_urls) if attachment_urls else ""
                    strike_details = f"{reason} {attachments_str}"

                    success = self.main_db.set_user_field(mention.id, f"strike_{total}", strike_details)
                    if total >= 3:
                        success = self.main_db.set_user_field(mention.id, "strikes", 0)
                        if success == 0:
                            user: discord.Member = ctx.guild.get_member(mention.id)
                            profile_pic = await get_profile_pic(user)
                            dead_or_alive_bytes = await draw_dead_or_alive('/assets/image_generator/wanted.png', profile_pic)
                            wanted_messageable = discord.File(fp=dead_or_alive_bytes, filename="wanted.png")
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
                            for strike in range(1, 4):
                                try:
                                    reason = self.main_db.get_user_field(mention.id, f"strike_{strike}")
                                    strike_reasons += f"Strike {strike}: {reason.decode('utf8')}\n"
                                except Exception as e:
                                    pass
                            
                            await user.add_roles(jail_role)
                            channel = self.bot.get_channel(self.confessional)
                            embed = discord.Embed(
                                title=f"You have been jailed for the following violations\n\n",
                                description=f"<@{mention.id}>\n\n{strike_reasons}",
                                color=0xFF0000
                            )
                            #embed.set_thumbnail(url=f"attachment://wanted.png")  # Set as thumbnail from file
                            embed.set_image(url="attachment://wanted.png")
                            # Add attachment URLs to the embed
                            if attachment_urls:
                                embed.add_field(
                                    name="Attachments",
                                    value='\n'.join(attachment_urls),
                                    inline=False
                                )

                            await channel.send(embed=embed, file=wanted_messageable)
                        else:
                            await ctx.send(f"Couldn't reset your strikes, contact an admin")
                    else:
                        await ctx.send(f"YOU EARNED A STRIKE <@{mention.id}> for {strike_details}\n TOTAL COUNT: {total}")
                else:
                    await ctx.send(
                        f"You cannot strike <@{mention.id}> because (s)he has not registered yet, <@{mention.id}> please use .register <your_league_name>")
    
    @commands.command()
    @super_user_check
    async def destroy(self, ctx: commands.Context, *args):
        mentions = ctx.message.mentions
        if len(mentions) != 1:
            await ctx.send("Mention ONE person to activate destruction mode.")
            return

        target_user = mentions[0]

        # Check if there's already an active target
        if self.active_destruction_target:
            if self.active_destruction_target == target_user.id:
                await ctx.send(f"Destruction mode is already active for {target_user.display_name}.")
                return
            else:
                # Stop the destruction for the previous target
                await ctx.send(f"Stopping destruction mode for the previous target.")
                self.active_destruction_target = None

        self.active_destruction_target = target_user.id
        await ctx.send(f"Destruction mode activated for {target_user.display_name}!")
        start_time = datetime.now(timezone.utc)  # Use timezone-aware datetime


        try:
            # Enter continuous destruction mode
            while self.active_destruction_target == target_user.id:
                # Check for and delete any messages sent by the target user in the current channel
                async for message in ctx.channel.history(limit=100):
                    if (message.author == target_user and 
                        message.created_at > start_time and 
                        message.channel.id != self.confessional):
                        confessional_channel = ctx.guild.get_channel(self.confessional)
                        await ctx.send(f"Don't type outside of {confessional_channel.mention}!")
                        await message.delete()

                # Attempt to disconnect the user if they're in a voice channel
                if target_user.voice and target_user.voice.channel:
                    await target_user.move_to(None)  # Disconnect from voice

                # Delay to prevent high resource usage and avoid rate limits
                await asyncio.sleep(5)

                # Check if the user is still in the server
                if not ctx.guild.get_member(target_user.id):
                    await ctx.send(f"{target_user.display_name} is no longer in the server. Stopping destruction mode.")
                    break

            # Clear the active target when the loop exits
            self.active_destruction_target = None

        except Exception as e:
            await ctx.send(f"An error occurred during destruction mode: {e}")
            self.active_destruction_target = None

    @commands.command()
    @super_user_check
    async def spare(self, ctx: commands.Context):
        """spare the current destruction mode target."""
        if not self.active_destruction_target:
            await ctx.send("There is no active destruction mode to stop.")
        else:
            self.active_destruction_target = None
            await ctx.send("Destruction mode stopped.")

async def setup(bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    print("adding discord commands...")
    await bot.add_cog(discMod(main_db, settings.JAILROLE, settings.CONFESSIONALCHANNELID, bot, 
                              settings.FANBOYROLEID, settings.HATERROLEID, settings.ROLECHANNELID, 
                              settings.CHANNELID, settings.PINGROLE, settings.LUNCHERS,
                              settings.LEAGUERSID, settings.VARIETYID))