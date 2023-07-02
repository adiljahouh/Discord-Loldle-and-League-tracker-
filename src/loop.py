from discord.ext import commands, tasks
import datetime
import discord

class loops(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        pass
    

    @commands.Cog.listener()
    async def on_ready(self):
        self.send_message.start()

    @tasks.loop(seconds=10)
    async def send_message(self):
        print("AAAAAAAAAH")
        current_time = datetime.datetime.utcnow().time()
        print(current_time)

        channel_id = self.bot.CHANNEL_ID  # Replace with the ID of the channel you want to send the message to
        channel = self.bot.get_channel(channel_id)
        if channel is not None:
            content = "Hello, Discord!"
            try:
                await channel.send(content)
                print("Message sent successfully.")
            except discord.Forbidden:
                print("I don't have permission to send messages to that channel.")
            except discord.HTTPException:
                print("Failed to send the message.")

async def setup(bot):
    await bot.add_cog(loops(bot))