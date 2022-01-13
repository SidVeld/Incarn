from discord.ext.commands import Cog, Context, group

from incarn.bot import IncarnBot


class Converters(Cog):
    """Usefull converters."""

    @group(name="convert", aliases=("cnvrt", "cnv", "conv"))
    async def converter(self, ctx: Context):
        """Simple converters that converts something to something."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # Temperature
    @converter.group(name="celsius", aliases=["c"])
    async def celsius(self, ctx: Context):
        """Convert degree Celsius to Fahrenheit or Kelvin."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @celsius.command(name="fahrenheit", aliases=["f"])
    async def celsius_to_fahrenheit(self, ctx: Context, temperature: float) -> None:
        """Convert degree Celsius to Fahrenheit."""
        fahrenheit = round((temperature * 1.8) + 32, 1)
        msg = f"{temperature}° Celsius is equal to {fahrenheit}° Fahrenheit."
        await ctx.send(msg)

    @celsius.command(name="kelvin", aliases=["k"])
    async def celsius_to_kelvin(self, ctx: Context, temperature: float) -> None:
        """Convert degree Celsius to Kelvin."""
        kelvin = round(temperature + 273.15, 1)
        msg = f"{temperature}° Celsius is equal to {kelvin}° Kelvin."
        await ctx.send(msg)

    @converter.group(aliases=["f"])
    async def fahrenheit(self, ctx: Context) -> None:
        """Convert Fahrenheit degree to Celsius or Kelvin."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @fahrenheit.command(name="celsius", aliases=["c"])
    async def fahrenheit_to_celsius(self, ctx: Context, temperature: float) -> None:
        """Convert Fahrenheit degree to Celsius."""
        celsius = round((temperature - 32) / 1.8, 1)
        msg = f"{temperature}° Fahrenheit is equal to {celsius}° Celsius."
        await ctx.send(msg)

    @fahrenheit.command(name="kelvin", aliases=["k"])
    async def fahrenheit_to_kelvin(self, ctx: Context, temperature: float) -> None:
        """Convert Fahrenheit degree to Kelvin."""
        kelvin = round((temperature - 32) * (5 / 9) + 273.15, 1)
        msg = f"{temperature}° Fahrenheit is equal to {kelvin}° Kelvin."
        await ctx.send(msg)

    @converter.group(aliases=["k"])
    async def kelvin(self, ctx: Context) -> None:
        """Convert Kelvin degree to Celsius or Fahrenheit."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @kelvin.command(name="celsius", aliases=["c"])
    async def kelvin_to_celsius(self, ctx: Context, temperature: float) -> None:
        """Convert Kelvin degree to Celsius."""
        celsius = round(temperature - 273.15, 1)
        msg = f"{temperature}° Kelvin is equal to {celsius}° Celsius."
        await ctx.send(msg)

    @kelvin.command(name="fahrenheit", aliases=["f"])
    async def kelvin_to_fahrenheit(self, ctx: Context, temperature: float) -> None:
        """Convert Kelvin degree to Fahrenheit."""
        fahrenheit = round((temperature - 273.15) * (9 / 5) + 32, 1)
        msg = f"{temperature}° Kelvin is equal to {fahrenheit}° Fahrenheit."
        await ctx.send(msg)

    # Weight
    @converter.group(name="pound", alieases=["pounds", "p"])
    async def pound(self, ctx: Context) -> None:
        """Convert pounds to kilograms."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @pound.group(name="kilogram", aliases=["kilograms", "kg"])
    async def pound_to_kilogram(self, ctx: Context, mass: float) -> None:
        """Convert pounds to kilograms."""
        kg = round((mass * 0.45359237), 1)
        await ctx.send(f"{mass} lb is equal to {kg} kg.")

    @converter.group()
    async def kilogram(self, ctx: Context) -> None:
        """Convert kilograms to pounds."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @kilogram.command(name="lb")
    async def kilogram_to_pounds(self, ctx: Context, mass: float) -> None:
        """Convert kilograms to pounds."""
        lb = round((mass / 0.45359237), 1)
        await ctx.send(f"{mass} kg is equal to {lb} lb.")

    # Distance
    @converter.group(name="mile", aliases=["miles", "m"])
    async def mile(self, ctx: Context):
        """Convert miles to kilometers."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @mile.command(name="kilometer", aliases=["kilometers", "kg"])
    async def mile_to_kilometer(self, ctx: Context, length: float) -> None:
        """Convert miles to kilometers."""
        km = round((length * 1.609344), 1)
        await ctx.send(f"{length} mi is equal to {km} km.")

    @converter.group()
    async def kilometer(self, ctx: Context):
        """Convert kilometers to miles."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @kilometer.command(name="mile", aliases=["miles", "m"])
    async def kilometer_to_mile(self, ctx: Context, length: float) -> None:
        """Convert kilometers to miles."""
        mi = round((length / 1.609344), 1)
        await ctx.send(f"{length} km is equal to {mi} mi.")


def setup(bot: IncarnBot) -> None:
    """Loads Converters cog."""
    bot.add_cog(Converters())
