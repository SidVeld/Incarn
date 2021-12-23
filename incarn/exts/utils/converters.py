from discord.ext import commands
from discord.ext.commands import Cog, Context

from incarn.bot import IncarnBot

ONE_KELVIN = 273.15


class Converters(Cog):
    """Usefull converters."""

    @commands.group(name="convert", aliases=("cnvrt", "cnv"))
    async def convert_command(self, ctx: Context):
        """Simple converters that converts something to something."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @convert_command.command(name="c2f")
    async def convert_c2f(self, ctx: Context, amount: float = 0):
        """Conversion of Celsius to Fahrenheit."""
        result = round((amount * 9 / 5) + 32, 2)
        await ctx.send(f"{amount}°C 🠖 {result}°F")

    @convert_command.command(name="f2c")
    async def convert_f2c(self, ctx: Context, amount: float = 0):
        """Convert Fahrenheit to Celsius."""
        result = round((amount - 32) * 9 / 5, 2)
        await ctx.send(f"{amount}°F 🠖 {result}°C")

    @convert_command.command(name="c2k")
    async def convert_c2k(self, ctx: Context, amount: float = 0):
        """Converts Celsius to Kelvin."""
        result = round(amount + ONE_KELVIN, 2)
        await ctx.send(f"{amount}°C 🠖 {result}K")

    @convert_command.command(name="k2c")
    async def convert_k2c(self, ctx: Context, amount: float = 0):
        """Converts Kelvins to Celsius."""
        result = round(amount - ONE_KELVIN, 2)
        await ctx.send(f"{amount}K 🠖 {result}°C")


def setup(bot: IncarnBot):
    bot.add_cog(Converters())
