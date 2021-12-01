from discord import Embed
from discord.ext import commands

from incarn.bot import IncarnBot
from incarn.constants import Colours


DESCRIPTIONS = (
    "Command processing time",
    "Python Discord website status",
    "Discord API latency"
)
ROUND_LATENCY = 3


class Latency(commands.Cog):
    """Getting the latency between the bot and websites."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Ping the bot to see its latency and state."""
        embed = Embed(
            title=":ping_pong: Pong!",
            colour=Colours.bright_green,
            description=f"Gateway Latency: {round(self.bot.latency * 1000)}ms",
        )

        await ctx.send(embed=embed)


def setup(bot: IncarnBot) -> None:
    """Load the Latency cog."""
    bot.add_cog(Latency(bot))
