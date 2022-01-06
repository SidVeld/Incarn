from discord import Embed
from discord.ext.commands import Cog, Context, command

from incarn.bot import IncarnBot


class KanyeQuote(Cog):
    """Commands for Kanye Rest Api."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot

    @command(name="kanye_quote", aliases=("kq", "kwq", "kanye", "kanyewest"))
    async def kanye_quote(self, ctx: Context):
        """Sends random Kanye West quote."""
        async with self.bot.http_session.get("https://api.kanye.rest") as response:

            if response.status != 200:
                await ctx.send(f"Something goes wrong. Code: {response.status}")
                return

            response = await response.json()
            quote = response["quote"]

            embed = Embed(
                title="Kanye West Quote",
                description=quote
            )

            await ctx.send(embed=embed)


def setup(bot: IncarnBot) -> None:
    """Load the KanyeQuote Cog."""
    bot.add_cog(KanyeQuote(bot))
