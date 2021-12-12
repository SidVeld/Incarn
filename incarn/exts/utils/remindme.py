import typing

from discord import Member
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.errors import BadArgument

from incarn.bot import IncarnBot
from incarn.log import get_logger
from incarn.utils.scheduling import Scheduler

log = get_logger(__name__)


class RemindMe(commands.Cog):
    """Cog for RemindMe command."""

    def __init__(self, bot: IncarnBot):
        self.bot = bot
        self.scheduler = Scheduler("RemindMeSchedule")

    def cog_unload(self) -> None:
        """Cancel the init task and scheduled tasks when the cog unloads."""
        log.trace("Cog unload: cancelling the channel queue tasks")
        for task in self.scheduler._scheduled_tasks.values():
            task.cancel()
        self.scheduler.cancel_all()

    @commands.command(name="remindme")
    async def remindme(self, ctx: Context, seconds: typing.Union[int, float], *reminder: str):
        """
        Reminds you after N-seconds to do something.
        """

        if seconds < 10:
            raise BadArgument("Time should be in seconds and more than 10")
        if len(reminder) < 1:
            raise BadArgument("Reminder should be longer than 1")

        new_reminder_id = len(self.scheduler._scheduled_tasks.items()) + 1

        embed = Embed()

        embed.description = f"You will be reminded in {seconds}"
        embed.set_author(name="Done!")

        await ctx.send(embed=embed)

        author: Member = ctx.author
        message = f"{author.mention}! you asked to remind that!"

        reminder = " ".join(reminder)

        embed.description = reminder
        embed.set_author(name="Your reminder")

        self.scheduler.schedule_later(seconds, new_reminder_id, ctx.send(message, embed=embed))


def setup(bot: IncarnBot):
    bot.add_cog(RemindMe(bot))
