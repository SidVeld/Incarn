from discord import Embed
from discord.ext.commands import Cog, Context, group

from incarn.bot import IncarnBot
from incarn.log import get_logger

log = get_logger(__name__)


class Covid19(Cog):
    """Information about Covid19."""

    def __init__(self, bot: IncarnBot):
        self.bot = bot

    @group(name="covid19", aliases=("covid", "covid2019"))
    async def covid(self, ctx: Context) -> None:
        """Commands for recieving information about covid-19 in world."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @covid.command(name="now")
    async def covid_now(self, ctx: Context, *, country: str = None):
        """Covid-19 Statistics for country."""

        all_alieases = ("all", "worldwide", "ww")

        if country in all_alieases or country is None:
            response = await self.bot.http_session.get("https://disease.sh/v3/covid-19/all")
        else:
            response = await self.bot.http_session.get(f"https://disease.sh/v3/covid-19/countries/{country.lower()}")

        if response.status == 200:
            response_json = await response.json(encoding="UTF-8")
        else:
            log.debug(f"Failed to get covid data. Status code {response.status}")
            await ctx.send(f"We got {response.status}.")
            return

        covid_information = [
            (":abacus: Total Cases", response_json["cases"]),
            (":coffin: Total Deaths", response_json["deaths"]),
            (":green_heart: Total Recover", response_json["recovered"]),
            (":mending_heart: Total Active Cases", response_json["active"]),
            (":warning: Total Critical Condition", response_json["critical"]),
            (":pencil: New Cases Today", response_json["todayCases"]),
            (":skull: New Deaths Today", response_json["todayDeaths"]),
            (":pill: New Recovery Today", response_json["todayRecovered"])
        ]

        embed = Embed()

        embed.colour = 0x77b15f

        embed.title = ":microbe: Covid-19"

        if country in all_alieases or country is None:
            embed.description = (
                f"Updated <t:{int(response_json['updated'] / 1000)}:R>"
                "\n────────────────────────"
            )
        else:
            embed.description = (
                f"Selected country: :flag_{response_json['countryInfo']['iso2'].lower()}: **{country.capitalize()}**\n"
                f"Updated <t:{int(response_json['updated'] / 1000)}:R>"
                "\n────────────────────────"
            )

        for name, value in covid_information:
            embed.add_field(
                name=name, value=f"{value:,}" if isinstance(value, int) else value
            )

        await ctx.send(embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(Covid19(bot))
