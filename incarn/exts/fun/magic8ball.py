import yaml
import random
from pathlib import Path

from discord.ext import commands

from incarn.bot import IncarnBot

ANSWERS = yaml.load(Path("incarn/resources/fun/magic8ball.yml").read_text("utf8"), Loader=yaml.FullLoader)


class Magic8ball(commands.Cog):
    """A Magic 8ball command to respond to a user's question."""

    @commands.command(name="8ball")
    async def output_answer(self, ctx: commands.Context, *, question: str) -> None:
        """Return a Magic 8ball answer from answers list."""
        answer = random.choice(ANSWERS)
        await ctx.reply(answer, mention_author=False)


def setup(bot: IncarnBot) -> None:
    """Load the Magic8Ball Cog."""
    bot.add_cog(Magic8ball())
