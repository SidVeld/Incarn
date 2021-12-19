from discord.ext import commands

from incarn.bot import IncarnBot

from zalgo_text import zalgo


class Zalgo(commands.Cog):
    """Text generator that turns text into zalgo-text."""

    @commands.command(name="zalgo")
    async def zalgo_generator(self, ctx: commands.Context, *, text: str) -> None:
        """H̱̿͢É̛̼ Ĉ̞̌O̡͎̝M̨̆͠E̵̅͘S̀̂͟"""
        text_zalgo = zalgo.zalgo().zalgofy(text)
        await ctx.reply(text_zalgo, mention_author=False)


def setup(bot: IncarnBot) -> None:
    """Load the Zalgo Cog."""
    bot.add_cog(Zalgo())
