from discord.ext import commands
from discord import Embed, Interaction, ButtonStyle
from discord.ui import View, button
from databases.main import MainDB
from typing import List, Tuple
from config import Settings
class PagerView(View):
    def __init__(self, main_db, author, page_size: int = 10):
        super().__init__(timeout=120)
        self.main_db   = main_db
        self.author    = author
        self.page_size = page_size
        self.page      = 1

    def build_embed(self) -> Embed:
        start = (self.page - 1) * self.page_size
        data  = self.main_db.get_all_users_sorted_by_field("points", True, start, self.page_size)

        if not data:
            title = "No more entries!"
            desc  = f"Page {self.page} is empty."
            body  = ""
        else:
            title = "Biggest gambling addicts 🃏"
            desc  = f"Page {self.page}"
            body  = "\n".join(
                f"{i+1+start}. <@{uid}> | {pts} pts"
                for i, (uid, pts) in enumerate(data)
            )

        embed = Embed(title=title, description=desc, color=0xFF0000)
        embed.add_field(name="Leaderboard", value=body or "—", inline=False)
        return embed

    async def _flip_page(self, interaction: Interaction, delta: int):
        # only the original user can navigate
        if interaction.user != self.author:
            return await interaction.response.send_message("🚫 Not for you!", ephemeral=True)

        # update page
        self.page = max(1, self.page + delta)
        # re-render
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @button(label="◀ Prev", style=ButtonStyle.primary)
    async def on_prev(self, interaction: Interaction, button):
        await self._flip_page(interaction, -1)

    @button(label="Next ▶", style=ButtonStyle.primary)
    async def on_next(self, interaction: Interaction, button):
        await self._flip_page(interaction, +1)
class leaderdBoardCommands(commands.Cog):
    def __init__(self, bot, main_db):
        self.bot     = bot
        self.main_db = main_db

    @commands.command()
    async def leaderboard(self, ctx: commands.Context):
        """
        Returns point leaderboard with Prev/Next buttons.
        """
        view = PagerView(self.main_db, ctx.author, page_size=10)
        await ctx.send(embed=view.build_embed(), view=view)

async def setup(bot: commands.Bot):
    settings = Settings()
    main_db = MainDB(settings.REDISURL)
    print("adding commands...")
    await bot.add_cog(leaderdBoardCommands(main_db=main_db, bot=bot))