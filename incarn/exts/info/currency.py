from textwrap import dedent

from discord import Embed
from discord.ext.commands import Cog, Context, group

from incarn.bot import IncarnBot
from incarn.log import get_logger

log = get_logger(__name__)

CURRENCY_API = "https://api.exchangerate-api.com/v4/latest/"


class Currency(Cog):
    """Commands for information about currency."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot

    @group(name="currency", aliases=("curr", "crrncy"))
    async def currency(self, ctx: Context) -> None:
        """Commands for information about currency."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @currency.command(name="get", aliases=("g",))
    async def currency_get(self, ctx: Context, currency: str = "USD") -> None:
        """
        Get information about currency.

        Sends embed, where provided information about currency
        in USD, EUR and RUB.
        """
        currency = currency.upper()

        response = await self.bot.http_session.get(f"{CURRENCY_API}{currency}")

        if response.status == 200:
            response_json = await response.json(encoding="UTF-8")
        else:
            log.debug(f"Failed to get covid data. Status code {response.status}")
            await ctx.send(f"We got {response.status}.")
            return

        base: str = response_json["base"]
        date: str = response_json["date"]
        rates: dict = response_json["rates"]

        embed = Embed()

        output = f"""
        **Date**: `{date}`

        **USD**: `{rates["USD"]}`
        **EUR**: `{rates["EUR"]}`
        **RUB**: `{rates["RUB"]}`
        """

        embed.title = base
        embed.description = dedent(output)

        await ctx.send(embed=embed)

    @currency.command(name="convert", aliases=("cnvert", "conv", "c"))
    async def currency_convert(self, ctx: Context, from_currency: str, to_currency: str, amount: int) -> None:
        """Converts currency from one currency to another currency."""

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            await ctx.send("1 : 1")
            return

        response = await self.bot.http_session.get(f"{CURRENCY_API}{to_currency}")

        if response.status == 200:
            response_json = await response.json(encoding="UTF-8")
        else:
            log.debug(f"Failed to get covid data. Status code {response.status}")
            await ctx.send(f"We got {response.status}.")
            return

        rates = response_json["rates"]
        date = response_json["date"]
        price = rates[from_currency]

        amount_converted = round(amount // price, 4)

        output = f"""
        **Date:** `{date}`
        **{to_currency}**: `{price}` **{from_currency}**

        `{amount}` **{from_currency}** -> `{amount_converted}` **{to_currency}**
        """
        embed = Embed()
        embed.description = dedent(output)

        await ctx.send(embed=embed)


def setup(bot: IncarnBot) -> None:
    """Loads currency extension."""
    bot.add_cog(Currency(bot))
