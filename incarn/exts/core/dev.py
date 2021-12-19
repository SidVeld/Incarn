import arrow
import psutil
import os
import platform
from pathlib import Path
from git import Repo

import discord
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.context import Context

from incarn.bot import IncarnBot


class Dev(Cog):
    """Usefull commands for developers."""

    def __init__(self, bot: IncarnBot):
        self.bot = bot
        self.process = psutil.Process(os.getpid())

    @commands.command(name="log")
    async def get_log(self, ctx: Context):
        """Sends log file to chat."""
        await ctx.author.send(file=discord.File(Path("logs/bot.log")))

    @commands.command(name="revision")
    async def revision(self, ctx: Context):
        """Sends technical information about the bot."""
        embed = discord.Embed()

        embed.set_author(name="Revision", icon_url=self.bot.user.avatar_url)

        embed.add_field(name="Date", value=arrow.utcnow().format("DD-MM-YYYY"))

        embed.add_field(name="Py-cord version", value=discord.__version__)

        embed.add_field(name="Python version", value=platform.python_version())

        ram_usage = self.process.memory_full_info().rss / 1024**2
        embed.add_field(name="RAM usage", value=f"{ram_usage:.2f} MB")

        embed.add_field(name="Last lauch", value=self.bot.start_time.humanize())

        embed.add_field(name="Branch", value=Repo("./").active_branch.name)

        embed.add_field(name="Last commit", value=Repo("./").active_branch.commit, inline=False)

        await ctx.send(embed=embed)

    async def cog_check(self, ctx: Context) -> bool:
        """Only allow owners to invoke the commands in this cog."""
        return await commands.is_owner().predicate(ctx)


def setup(bot: IncarnBot) -> None:
    bot.add_cog(Dev(bot))
