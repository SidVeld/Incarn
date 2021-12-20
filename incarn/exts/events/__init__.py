from incarn.bot import IncarnBot
from ._cog import Events


def setup(bot: IncarnBot) -> None:
    bot.add_cog(Events(bot))
