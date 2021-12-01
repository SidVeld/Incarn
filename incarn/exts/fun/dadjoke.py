from discord.ext import commands

from incarn.bot import IncarnBot


class DadJoke(commands.Cog):
    """Cog for the dadjoke command."""

    def __init__(self, bot: IncarnBot):
        self.bot = bot

    @commands.command()
    async def dadjoke(self, ctx: commands.Context):
        """Gets a random dad joke."""
        url = "https://icanhazdadjoke.com/"

        async with self.bot.http_session.get(url, headers={"Accept": "text/plain"}) as response:
            result = await response.text(encoding="UTF-8")
            await ctx.send(result)


def setup(bot: IncarnBot):
    """Loads the dadjoke cog"""
    bot.add_cog(DadJoke(bot))
