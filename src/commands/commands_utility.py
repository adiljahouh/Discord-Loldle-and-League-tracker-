from redis.exceptions import ConnectionError
from config import Settings
import functools
from databases.main_db import MainDB


def role_check(func):
    @functools.wraps(func)
    async def inner(self, ctx, *args, **kwargs):
        try:
            redisdb = MainDB(Settings().REDISURL)
            discord_ids: list[bytes] = redisdb.get_all_users()
            ids = [id.decode('utf-8') for id in discord_ids]
            for id in ids:
                if str(id) == str(ctx.author.id):
                    return await func(self, ctx, *args, **kwargs)
            await ctx.send("You need to register using .register <league_name> to use this bot.")
        except ConnectionError as e:
            print("Role_check: ", e)
            await ctx.send("Could not connect to database to verify users.")
            return
    return inner


def mod_check(func):
    @functools.wraps(func)
    async def inner(self, ctx, *args, **kwargs):
        print("In mod_check")
        try:
            for role in ctx.author.roles:
                if role.id == self.player_role:
                    print("Moderator validated")
                    return await func(self, ctx, *args, **kwargs)
            required_role = ctx.guild.get_role(self.player_role)
            await ctx.send(f"You need the {required_role.mention} role to use this command.")
        except Exception as e:
            await ctx.send(f"Error occured during role check, Error: {e}")
            return
    return inner
