from discord.ext import commands
from discord.ext.commands import Cog, Context

from incarn.bot import IncarnBot


class Converters(Cog):
    """Usefull converters."""

    def __init__(self, bot: IncarnBot):
        self.bot = bot

    @commands.command()
    async def c2f(self, ctx: Context, amount: float = 0) -> None:
        """Conversion of Celsius to Fahrenheit."""
        result = round((amount * 9 / 5) + 32, 2)
        await ctx.send(f"{amount}°C 🠖 {result}°F")

    @commands.command()
    async def f2c(self, ctx: Context, amount: float = 0) -> None:
        """Convert Fahrenheit to Celsius."""
        result = round((amount - 32) / 1.8, 2)
        await ctx.send(f"{amount}°F 🠖 {result}°C")

    @commands.command()
    async def c2k(self, ctx: Context, amount: float = 0) -> None:
        """Converts Celsius to Kelvin."""
        result = round(amount + 273.15, 2)
        await ctx.send(f"{amount}°C 🠖 {result}K")

    @commands.command()
    async def k2c(self, ctx: Context, amount: float = 0) -> None:
        """Converts Kelvins to Celsius."""
        result = round(amount - 273.15, 2)
        await ctx.send(f"{amount}K 🠖 {result}°C")

    @commands.command()
    async def hex2rgb(self, ctx: Context, hex_code: str = "#FFFFFF") -> None:
        """Converts HEX to RGB."""
        if hex_code.startswith("#"):
            hex_code = hex_code.replace("#", "")
        rgb_code = tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))
        await ctx.send(f"HEX: #{hex_code} 🠖 RGB: {rgb_code}")

    @commands.command()
    async def rgb2hex(self, ctx: Context, r=255, g=255, b=255) -> None:
        """Converts RGB to HEX."""
        hex_code = "#%02x%02x%02x" % (r, g, b)
        await ctx.send(f"RGB: ({r}, {g}, {b}) 🠖 HEX: {hex_code}")

    # @commands.command()
    # async def color(self, ctx: Context, hex_code: str) -> None:
    #     """Generates colored embed."""

    #     if hex_code.startswith("#"):
    #         hex_code = hex_code.replace("#", "")

    #     embed = discord.Embed(description=f"HEX: `#{hex_code}`", color=int(hex_code, 16))
    #     embed.set_image(url=f"http://placehold.it/240x120.png/{hex_code}/{hex_code}")

    #     await ctx.send(embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(Converters(bot))
