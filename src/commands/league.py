from discord.ext import commands
from api.riot import riotAPI
import aiohttp
from config import Settings
import discord
from commands.utility.decorators import role_check, mod_check, super_user_check
from databases.main import MainDB
from databases.stalker import StalkingDB

## why do i even inherit riotapi here?
class LeagueCommands(commands.Cog):
    def __init__(self, main_db: MainDB, stalking_db: StalkingDB, riot_api: riotAPI,
                  player_role_id: int, g_role: int, jail_role: int) -> None:
        self.main_db = main_db
        self.stalking_db = stalking_db
        self.riot_api= riot_api
        self.player_role = player_role_id
        self.g_role = g_role
        self.jail_role = jail_role

    @commands.Cog.listener()
    async def on_ready(self):
        pass   
    
    @commands.command()
    async def register(self, ctx: commands.Context, *args):
        """ Register a user by calling .register <your_league_name>"""
        async with ctx.typing():
            has_jail_role = any(role.id == self.jail_role for role in ctx.author.roles)
            if has_jail_role:
                await ctx.send("HAHAHAHAHAHAH LOL!!! CONFESS YOUR SINS TO THE JUDGES")
                return
            print("register")
            riot_name = "".join(args)
            if len(riot_name) == 0 or '#' not in riot_name:
                await ctx.send("Specify a riot user and tag (e.g. .register mocro#zpr)")
                return
            user, tag = riot_name.split('#')
            author_discord_tag = str(ctx.author)
            discord_userid = str(ctx.author.id)
            try:
                puuid = await self.riot_api.get_puuid_by_tag(user, tag)
            except aiohttp.ClientResponseError as e:
                if 400 <= e.status <= 500:
                    message = "Bad request error, make sure you pass a valid summoner name"
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
            \n**Discord Tag:** {author_discord_tag}\n**Riot User:** {riot_name}\n**Strikes:** {user['strikes']}\n**Points:** {user['points']}\n**Strike Quota:** {user['strike_quota']}"
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
    async def count(self, ctx: commands.Context):
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
    async def summary(self, ctx: commands.Context, *args):

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
                        riot_name = "".join(args[:-1])
                        queue_id = [i for i in game_mode_mapping if game_mode_mapping[i] == args[-1]][0]
                    else:
                        riot_name = "".join(args)
                        queue_id = None
                    if '#' in riot_name:
                        user, tag = riot_name.split('#')
                        message = await self.riot_api.get_kda_by_user(user, tag, count, queue_id)
                    else:
                        await ctx.send("add a tag (e.g. Mocro#zpr)")
                        return
                else:
                    puuid = self.main_db.get_user_field(str(ctx.author.id), "puuid")
                    message = await self.riot_api.get_kda_by_puuid(puuid.decode('utf-8'), count)
            except aiohttp.ClientResponseError as e:
                if 400 <= e.status <= 500:
                    message = "Bad request, make sure you pass a valid summoner name and game mode (solo, flex, normals, aram, clash, ranked)"
                else:
                    message = "Internal Server Error"
                await ctx.send(message)
                return
            finally:
                embed = discord.Embed(title=f"📓Summary of last {count} games📓\n\n",
                                      description=f"{message}",
                                      color=0xFF0000)
                await ctx.send(embed=embed)

                
    @commands.command()
    @role_check
    async def rank(self, ctx: commands.Context, *args):

        """ Temporary command to get the rank of a user"""
        async with ctx.typing():
            try:
                # if we pass a name
                if len(args) != 0:
                    riot_name: str = "".join(args)
                    if '#' in riot_name:
                        # get puuid from test#100
                        user, tag = riot_name.split('#')
                        print(user, tag)
                        puuid = await self.riot_api.get_puuid_by_tag(user, tag)
                    else:
                        await ctx.send("You didnt include a tag seperated by #, such as Mocro#zpr")
                # if we dont pass a name
                else:
                    puuid = self.main_db.get_user_field(str(ctx.author.id), "puuid").decode('utf-8')
                id = await self.riot_api.get_encrypted_summoner_id_by_puuid(puuid)
                soloq_info = await self.riot_api.get_soloq_info_by_encrypted_id(id)
                if soloq_info is None:
                    await ctx.send("User apparently doesnt play SOLOQ")
                    return
                message = f"W/L {soloq_info['wins']}/{soloq_info['losses']}\n Winrate {round(((soloq_info['wins']/(soloq_info['losses'] + soloq_info['wins']))*100), 2)}%"
            except aiohttp.ClientResponseError as e:
                if 400 <= e.status <= 500:
                    message = "Bad request error, make sure you pass a valid summoner name and game mode (solo, flex, normals, aram, clash, ranked)"
                else:
                    message = "Server side error from RIOT, this could affect other commands regarding league"
                await ctx.send(message)
                return
            finally:
                try:
                    print(soloq_info)
                    picture = discord.File(fp=f"./assets/ranks/{soloq_info['tier'].upper()}.png", filename=f"{soloq_info['tier'].upper()}.png")
                    embed = discord.Embed(title=f"SOLODUO {soloq_info['tier']} {soloq_info['rank']} {soloq_info['leaguePoints']} LP\n",
                                        description=f"{message}",
                                        color=0xFF0000)
                    embed.set_thumbnail(url=f"attachment://{soloq_info['tier'].upper()}.png")
                    await ctx.send(embed=embed, file=picture)
                except Exception as e:
                    print(e)
    @commands.command()
    @role_check
    async def clash(self, ctx: commands.Context, *args):
        """
            Returns the opgg of all members in the same clash team as the given summoner name
        """
        async with ctx.typing():
            summoner = "".join(args)
            if '#' not in summoner:
                await ctx.send("Add a summoner with a user and tag (e.g. mocro#zpr)")
                return
            user, tag = summoner.split('#')
            message = ""
            embed = False
            try:
                if len(args) != 0:
                    opgg = await self.riot_api.get_clash_opgg(user=user, tag=tag)
                    message = opgg
                    embed = True
                else:
                    message = "Please provide a valid summoner name: .clash <summoner name>"
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
    async def victim(self, ctx: commands.Context, *args):
        """
            Add or remove a stalking victim: .victim <add/remove> <ign>
        """
        async with ctx.typing():
            if len(args) < 2:
                await ctx.send("Use .stalk <add/remove> <ign#tag>")
                return
            elif args[0] != "add" and args[0] != "remove":
                await ctx.send("Use .stalk <add/remove> <ign#tag>")
                return
            summoner = " ".join(args[1:]).lower()
            if '#' not in summoner and args[0] == "add": # bit silly but this is to enable removing junk
                await ctx.send("Use .stalk <add/remove> <ign#tag>")
                return
            if args[0] == "add":
                total_users = self.stalking_db.get_all_users()
                if len(total_users) >= 5:
                    await ctx.send("You can only stalk 5 users at a time, remove one first")
                    return
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
    async def victims(self, ctx: commands.Context):
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


async def setup(bot: commands.Bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    stalking_db = StalkingDB(settings.REDISURL)
    riot_api = riotAPI(settings.RIOTTOKEN)
    print("adding commands...")
    await bot.add_cog(LeagueCommands(main_db, stalking_db, riot_api, settings.PLAYERROLE, settings.GROLE, settings.JAILROLE))
