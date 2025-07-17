from discord.ext import commands
from discord import Embed, Interaction, ButtonStyle
from discord.ui import View, button
from databases.main import MainDB
from config import Settings

class PagerView(View):
    def __init__(self, main_db: MainDB, author, category: str = "points", page_size: int = 10):
        super().__init__(timeout=120)
        self.main_db   = main_db
        self.author    = author
        self.page_size = page_size
        self.page      = 1
        self.category  = category

        # mapping of command categories to Redis fields and embed titles
        self.category_map = {
            "points":      ("points", "Biggest gambling addicts 🃏"),
            "strikes":     ("total_strikes",   "Most strikes 👮‍♂️"),
            "honors":      ("total_honors",    "Top honors 🏅"),
        }

    def build_embed(self) -> Embed:
        # resolve actual Redis field and title for this category
        redis_field, title = self.category_map.get(
            self.category,
            ("points", "Leaderboard")
        )

        start = (self.page - 1) * self.page_size
        data  = self.main_db.get_all_users_sorted_by_field(
            redis_field, True, start, self.page_size
        )

        if not data:
            desc = f"Page {self.page} is empty."
            body = ""
        else:
            desc = f"Page {self.page} • Sorted by `{self.category}`"
            body = "\n".join(
                f"{i+1+start}. <@{uid}> | {pts} {self.category}"
                for i, (uid, pts) in enumerate(data)
            )

        embed = Embed(title=title, description=desc, color=0xFF0000)
        embed.add_field(name="Leaderboard", value=body or "—", inline=False)
        return embed

    async def _flip_page(self, interaction: Interaction, delta: int):
        if interaction.user != self.author:
            return await interaction.response.send_message("🚫 Not for you!", ephemeral=True)
        self.page = max(1, self.page + delta)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @button(label="◀ Prev", style=ButtonStyle.primary)
    async def on_prev(self, interaction: Interaction, button):
        await self._flip_page(interaction, -1)

    @button(label="Next ▶", style=ButtonStyle.primary)
    async def on_next(self, interaction: Interaction, button):
        await self._flip_page(interaction, +1)

class LeaderboardCommands(commands.Cog):
    def __init__(self, bot, main_db: MainDB):
        self.bot     = bot
        self.main_db = main_db

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx: commands.Context, *args):
        """
        Usage: .leaderboard <category> [page]
        Categories: `points`, `strikes`, `honors`
        Example: .leaderboard strikes 2
        """
        if not args:
            return await ctx.send("Please specify one category: `points`, `strikes`, or `honors`. Optionally follow with a page number.")

        category = args[0].lower()
        if category not in ("points", "strikes", "honors"):
            return await ctx.send(f"Unknown category `{category}`. Choose from `points`, `strikes`, or `honors`.")

        # parse optional page
        page = 1
        if len(args) > 1:
            try:
                page = max(1, int(args[1]))
            except ValueError:
                return await ctx.send("Page must be a positive integer.")

        view = PagerView(self.main_db, ctx.author, category=category, page_size=10)
        view.page = page
        await ctx.send(embed=view.build_embed(), view=view)

async def setup(bot: commands.Bot):
    settings = Settings()
    main_db  = MainDB(settings.REDISURL)
    print("Adding LeaderboardCommands")
    await bot.add_cog(LeaderboardCommands(bot, main_db))
