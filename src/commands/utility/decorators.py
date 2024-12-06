from redis.exceptions import ConnectionError
from config import Settings
import functools
from databases.main import MainDB


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
        settings = Settings()
        try:
            for role in ctx.author.roles:
                if role.id == settings.PLAYERROLE:
                    print("Moderator validated")
                    return await func(self, ctx, *args, **kwargs)
            required_role = ctx.guild.get_role(settings.PLAYERROLE)
            await ctx.send(f"You need the {required_role.mention} role to use this command.")
        except Exception as e:
            await ctx.send(f"Error occured during role check, Error: {e}")
            return
    return inner

def jailed_check(func):
    @functools.wraps(func)
    async def inner(self, ctx, *args, **kwargs):
        settings = Settings()
        try:
            for role in ctx.author.roles:
                if role.id == settings.JAILROLE:
                    print("Jailee validated")
                    return await func(self, ctx, *args, **kwargs)
            await ctx.send(f"You need to be in JAIL to use this command")
        except Exception as e:
            await ctx.send(f"Error occured during role check, Error: {e}")
            return
    return inner

def super_user_check(func):
    @functools.wraps(func)
    async def inner(self, ctx, *args, **kwargs):
        settings = Settings()
        try:
            if str(ctx.author.id) == str(settings.SUPERUSER):
                print("super user validated")
                return await func(self, ctx, *args, **kwargs)
            else:
                await ctx.send(f"You are not <@{settings.SUPERUSER}>")
        except Exception as e:
            await ctx.send(f"Error: {e}")
            return
    return inner


def fix_highlighted_player(main_db, betting_db, stalking_db):
    active = stalking_db.get_active_user()
    if active is None:
        return
    stalking_db.change_status(active, False)
    all_bets = betting_db.get_all_bets()
    for decision in all_bets.keys():
        for user in all_bets[decision]:
            main_db.increment_field(user['discord_id'], "points", int(user['amount']))
            print(f"Refunding: {user['discord_id']}, {int(user['amount'])}")
    betting_db.remove_all_bets()
