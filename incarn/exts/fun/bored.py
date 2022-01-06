from discord import Embed
from discord.ext.commands import Cog, Context, command

from incarn.bot import IncarnBot


class Bored(Cog):
    """Commands for BoredApi."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot

    # TODO: add subcommands for this api
    @command(name="bored", aliases=("imbored", "whattodo", "brd"))
    async def bored(self, ctx: Context):
        """Bored? This team will give you an idea of what you can do."""
        async with self.bot.http_session.get("https://www.boredapi.com/api/activity/") as response:

            if response.status != 200:
                await ctx.send(f"Something goes wrong. Code: {response.status}")
                return

            json_dict = await response.json()
            act_name: str = json_dict["activity"]
            act_type: str = json_dict["type"]
            act_part: int = json_dict["participants"]
            act_link: str = json_dict["link"]
            act_key: str = json_dict["key"]

            embed = Embed()

            embed.set_author(name="Bored?")

            embed.description = act_name

            embed.add_field(name="Type", value=act_type.capitalize())
            embed.add_field(name="Participants", value=act_part)
            embed.add_field(name="Key", value=act_key)

            if act_link != "":
                embed.add_field(
                    name="Link",
                    value=act_link,
                    inline=False
                )

            await ctx.send(embed=embed)


def setup(bot: IncarnBot) -> None:
    """Load the KanyeQuote Cog."""
    bot.add_cog(Bored(bot))
