import arrow
from dateutil.relativedelta import relativedelta

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Context

from incarn.bot import IncarnBot
from incarn.constants import Colours


DESCRIPTIONS = (
    "Command processing time",
    "Python Discord website status",
    "Discord API latency"
)
ROUND_LATENCY = 3


class Latency(commands.Cog):
    """Getting the latency and uptime of the bot."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: Context) -> None:
        """Ping the bot to see its latency and state."""
        embed = Embed(
            title=":ping_pong: Pong!",
            colour=Colours.bright_green,
            description=f"Gateway Latency: {round(self.bot.latency * 1000)}ms",
        )

        await ctx.send(embed=embed)

    @commands.command(name="uptime")
    async def uptime(self, ctx: Context) -> None:
        """Get the current uptime of the bot."""
        difference = relativedelta(self.bot.start_time - arrow.utcnow())
        uptime_string = self.bot.start_time.shift(
          seconds=difference.seconds,
          minutes=difference.minutes,
          hours=difference.hours,
          days=difference.days,
        ).humanize()

        await ctx.send(f"I started working {uptime_string}!")


def setup(bot: IncarnBot) -> None:
    """Load the Latency cog."""
    bot.add_cog(Latency(bot))
