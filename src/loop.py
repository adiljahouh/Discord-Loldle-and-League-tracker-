from discord.ext import commands, tasks
import datetime
import discord

class loops(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        pass
    

    @commands.Cog.listener()
    async def on_ready(self):
        await self.send_message.start()

    @tasks.loop(seconds=1000)
    async def send_message(self):
        print("⏰ ITS EXPOSING TIME ⏰\n\n\
              ")
        user = self.bot.users # get all users
        channel_id = self.bot.CHANNEL_ID  # Replace with the ID of the channel you want to send the message to
        channel = self.bot.get_channel(channel_id)
        if channel is not None:
            """
            query redis db for all users, check recents kdas and retrieve the cumulative worst.
            
            """
            content = ""
            try:
                await channel.send(content)
                print("Message sent successfully.")
            except discord.Forbidden:
                print("I don't have permission to send messages to that channel.")
            except discord.HTTPException:
                print("Failed to send the message.")

async def setup(bot):
    print("adding loops..")
    await bot.add_cog(loops(bot))