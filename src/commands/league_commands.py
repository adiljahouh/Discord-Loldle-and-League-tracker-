from discord.ext import commands
from api.riot import riotAPI
import aiohttp
from config import Settings
import discord
from commands.commands_utility import role_check, mod_check, super_user_check
from databases.main_db import MainDB
from databases.stalking_db import StalkingDB


class LeagueCommands(riotAPI, commands.Cog):
    def __init__(self, main_db, stalking_db, riot_api, player_role_id, g_role, jail_role) -> None:
        self.main_db = main_db
        self.stalking_db = stalking_db
        self.riot_api: riotAPI = riot_api
        self.player_role = player_role_id
        self.g_role = g_role
        self.jail_role = jail_role

    @commands.Cog.listener()
    async def on_ready(self):
        pass


    @commands.command()
    async def register(self, ctx, *args):
        """ Register a user by calling .register <your_league_name>"""
        async with ctx.typing():

            has_jail_role = any(role.id == self.jail_role for role in ctx.author.roles)
            if has_jail_role:
                await ctx.send("HAHAHAHAHAHAH LOL!!! CONFESS YOUR SINS TO THE JUDGES")
                return
            print("register")
            riot_name = "".join(args)
            if len(riot_name) == 0:
                await ctx.send("Specify a riot username")
                return
            author_discord_tag = str(ctx.author)
            discord_userid = str(ctx.author.id)
            try:
                puuid = await self.riot_api.get_puuid(riot_name)
            except aiohttp.ClientResponseError as e:
                if 400 <= e.status <= 500:
                    message = "Bad request error, refresh the API key or re-register your user"
                else:
                    message = "Internal Server Error"
                await ctx.send(message)
                return
            print(self.main_db.check_user_existence(discord_userid))
            if self.main_db.check_user_existence(discord_userid) != 1:
                print("doesnt exists")
                self.main_db.store_user(discord_userid, riot_name, puuid, author_discord_tag)
                response = f"**Discord ID**: {discord_userid}\
                \n**Discord Tag:** {author_discord_tag}\n**Riot User:** {riot_name}\n**Strikes:** 0\n**Points:** 500"
            else:
                print("exists")
                try:
                    self.main_db.set_user_field(discord_userid, "riot_user", riot_name)
                    self.main_db.set_user_field(discord_userid, "puuid", puuid)
                    user :dict = self.main_db.get_user(discord_userid)
                except Exception as ex:
                    print(ex)
                response = f"**Discord ID**: {discord_userid}\
            \n**Discord Tag:** {author_discord_tag}\n**Riot User:** {riot_name}\n**Strikes:** {user['strikes']}\n**Points:** {user['points']}"
            try:
                g_role = ctx.guild.get_role(self.g_role)
                await ctx.author.add_roles(g_role)
            except Exception as e:
                await ctx.send(e)
                return
            embed = discord.Embed(title="📠Registering User📠\n\n",
                                  description=f"{response}",
                                  color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.command()
    @role_check
    @mod_check
    async def count(self, ctx):
        """
            Returns amount of users registered
        """
        print("Counting")
        async with ctx.typing():
            discord_ids: list[bytes] = self.main_db.get_all_users()
            response = ''
            for index, discord_id in enumerate(discord_ids):
                id = discord_id.decode('utf-8')
                response += f'\n{index + 1}. <@{id}>'
            embed = discord.Embed(title="📠Users Registered📠\n\n",
                                  description=f"{response}",
                                  color=0xFF0000)
            await ctx.send(embed=embed)

    # @commands.command()
    # @mod_check
    # async def deregister(self, ctx):
    #     """ deregister a user by calling .deregister <your_league_name>"""
    #     async with ctx.typing():
    #         author_discord_tag = str(ctx.author)
    #         userid = str(ctx.author.id)
    #         userinfo: dict = self.main_db.remove_and_return_all(userid)
    #         if userinfo is not None:
    #             response = f"**Riot ID**: {userid}\
    #             \n**Discord Tag:** {author_discord_tag}\n**Riot User:** {userinfo[b'riot_user'].decode('utf-8')}\n" \
    #                 f"**Strikes:** {userinfo[b'strikes'].decode('utf-8')}"
    #         else:
    #             response = "No user found for discord ID"
    #         embed = discord.Embed(title="📠Deregistering User📠\n\n",
    #                               description=f"{response}",
    #                               color=0xFF0000)
    #         await ctx.send(embed=embed)

    @commands.command()
    @role_check
    async def summary(self, ctx, *args):

        """ Summary of a user (or your registered user if nothing is passed)
          by calling .summary <league_name> or just .summary"""
        async with ctx.typing():
            game_mode_mapping = {
                0: "custom",
                400: "normal",
                420: "solo",
                430: "blind",
                440: "flex",
                450: "aram",
                700: "clash",
                1700: "arena",
                "ranked": "ranked",
                "normal": "normals"
            }
            try:
                count = 5
                if len(args) != 0:
                    if args[-1].lower() in game_mode_mapping.values():
                        user = "".join(args[:-1])
                        queue_id = [i for i in game_mode_mapping if game_mode_mapping[i] == args[-1]][0]
                    else:
                        user = "".join(args)
                        queue_id = None
                    message = await self.riot_api.get_kda_by_user(user, count, queue_id)
                else:
                    puuid = self.main_db.get_user_field(str(ctx.author.id), "puuid")
                    message = await self.riot_api.get_kda_by_puuid(puuid.decode('utf-8'), count)
            except aiohttp.ClientResponseError as e:
                if 400 <= e.status <= 500:
                    message = "Bad request error, refresh the API key or re-register your user"
                else:
                    message = "Internal Server Error"
            finally:
                embed = discord.Embed(title=f"📓Summary of last {count} games📓\n\n",
                                      description=f"{message}",
                                      color=0xFF0000)
                await ctx.send(embed=embed)


    @commands.command()
    @role_check
    async def rank(self, ctx, *args):

        """ Temporary command to get the rank of a user"""
        async with ctx.typing():
            try:
                if len(args) != 0:
                    user = "".join(args)
                else:
                    puuid = self.main_db.get_user_field(str(ctx.author.id), "puuid")
                    user = await self.riot_api.get_name_by_summoner_puuid(puuid.decode('utf-8'))
                soloq_info = await self.riot_api.get_soloq_info_by_name(user)
                if soloq_info is None:
                    await ctx.send("User apparently doesnt play SOLOQ")
                    return
                message = f"W/L {soloq_info['wins']}/{soloq_info['losses']}\n Winrate {round(((soloq_info['wins']/(soloq_info['losses'] + soloq_info['wins']))*100), 2)}%"
            except aiohttp.ClientResponseError as e:
                if 400 <= e.status <= 500:
                    message = "Bad request error, refresh the API key or re-register your user"
                else:
                    message = "Internal Server Error"
            finally:
                try:
                    picture = discord.File(fp=f"/assets/ranks/{soloq_info['tier'].upper()}.png", filename=f"{soloq_info['tier'].upper()}.png")
                    embed = discord.Embed(title=f"SOLODUO {soloq_info['tier']} {soloq_info['rank']} {soloq_info['leaguePoints']} LP\n",
                                        description=f"{message}",
                                        color=0xFF0000)
                    embed.set_thumbnail(url=f"attachment://{soloq_info['tier'].upper()}.png")
                    await ctx.send(embed=embed, file=picture)
                except Exception as e:
                    print(e)
    @commands.command()
    @role_check
    async def clash(self, ctx, *args):
        """
            Returns the opgg of all members in the same clash team as the given summoner name
        """
        async with ctx.typing():
            summoner = "".join(args)
            message = ""
            embed = False
            try:
                if len(args) != 0:
                    opgg = await self.riot_api.get_clash_opgg(summoner)
                    message = opgg
                    embed = True
                else:
                    message = "Pls provide a valid summoner name: .clash <summoner name>"
            except aiohttp.ClientResponseError as e:
                if 400 <= e.status <= 500:
                    message = "Bad request error, invalid summoner"
                else:
                    message = "Internal Server Error"
            finally:
                if embed:
                    embed = discord.Embed(title=f"Clash team opgg for player: {summoner}\n\n", description=f"{message}",
                                          color=0xFF0000)
                    await ctx.send(embed=embed)
                else:
                    if message == "":
                        message = "Player is not in a clash team"
                    await ctx.send(message)

    @commands.command()
    @mod_check
    async def victim(self, ctx, *args):
        """
            Add or remove a stalking victim: .victim <add/remove> <ign>
        """
        async with ctx.typing():
            if len(args) < 2:
                await ctx.send("Use .stalk <add/remove> <ign>")
                return
            elif args[0] != "add" and args[0] != "remove":
                await ctx.send("Use .stalk <add/remove> <ign>")
                return
            summoner = " ".join(args[1:]).lower()
            if args[0] == "add":
                self.stalking_db.store_user(summoner)
                embed = discord.Embed(title=f"Victim added: {summoner}",
                                      color=0xFF0000)
            else:
                self.stalking_db.remove_user(summoner)
                embed = discord.Embed(title=f"Victim removed: {summoner}",
                                      color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.command()
    @role_check
    async def victims(self, ctx):
        """
            Return all victims
        """
        users = self.stalking_db.get_all_users()
        desc = ""
        for user in users:
            desc += f"\n{user}"
        embed = discord.Embed(title=f"Stalking Victims", description=f"{desc}",
                              color=0xFF0000)
        await ctx.send(embed=embed)


async def setup(bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    stalking_db = StalkingDB(settings.REDISURL)
    riot_api = riotAPI(settings.RIOTTOKEN, bot.get_tokenbucket())
    print("adding commands...")
    await bot.add_cog(LeagueCommands(main_db, stalking_db, riot_api, settings.PLAYERROLE, settings.GROLE, settings.JAILROLE))
