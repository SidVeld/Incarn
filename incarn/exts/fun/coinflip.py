import random

from discord.ext import commands

from incarn.bot import IncarnBot


class CoinFlip(commands.Cog):
    """Cog for coinflip command."""

    @commands.command(name="coinflip", aliases=("flip", "coin", "cf"))
    async def coinflip_command(self, ctx: commands.Context, side1: str = "heads", side2: str = "tails") -> None:
        """
        Flips a coin.

        You can customize sides of your coin.
        Replace `side1` and `side2` with your params.
        """
        flipped_side = random.choice([side1, side2])
        message = f"{ctx.author.name} flipperd a coin and got: **{flipped_side}**"
        await ctx.send(message)


def setup(bot: IncarnBot) -> None:
    """Load the coinflip cog."""
    bot.add_cog(CoinFlip())
