import arrow
import yaml
from arrow import Arrow
from pathlib import Path
from typing import Optional

from discord import Embed
from discord.channel import TextChannel
from discord.ext import tasks, commands
from discord.ext.commands import Cog, command, Context

from incarn.bot import IncarnBot
from incarn.constants import Channels
from incarn.log import get_logger
from incarn.utils import scheduling


log = get_logger(__name__)

EVENTS_DIR = Path("incarn/resources/events")


class Events(Cog):
    """
    This module allows the bot to track holidays known to it
    and remind everyone about them on the server.
    """

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot
        self.scheduler = scheduling.Scheduler("EventsScheduler")
        self._plan_fetch_task = scheduling.create_task(self._plan_fetch(), event_loop=self.bot.loop)

    def cog_unload(self) -> None:
        self.scheduler.cancel_all()
        self.check_day.stop()

    async def _plan_fetch(self) -> None:
        today = arrow.now()
        next_day = today.shift(days=1)
        next_day_midnight = next_day.replace(hour=0, minute=1, second=0, microsecond=0)
        self.scheduler.schedule_at(next_day_midnight, 1, self._start_checking())

    async def _start_checking(self) -> None:
        self.check_day.start()

    @tasks.loop(hours=24)
    async def check_day(self) -> None:
        """Checks day for special events."""
        today = arrow.now()
        await self.fetch_birthdays(today)
        await self.fetch_holidays(today)

    async def fetch_birthdays(self, today: Arrow) -> None:
        """Fetches birthdays and sending embed if today is someone's burthday."""
        today_str = today.format("DD-MM")
        log.debug(f"Fetching birthdays with {today_str}")

        b_file = EVENTS_DIR / "birthdays.yml"
        birthdays: dict = yaml.load(b_file.open(encoding="UTF-8"), Loader=yaml.FullLoader)

        for birthday in birthdays.values():

            if birthday["date"] != today_str:
                continue

            name: str = birthday["name"]
            text: str = birthday["text"]
            date: str = birthday["date"]
            year: Optional[int] = birthday["year"]

            log.trace(f"Found birthday: {name}. Builing embed.")

            embed = Embed(
                title=f":birthday: Today is the birthday of: {name}",
                description=text,
                colour=0xec586d
            )

            embed.add_field(name="Date of birth", value=date)

            if year is not None:
                embed.add_field(name="Age as of today", value=int(today.format("YYYY")) - year)

            embed.set_footer(text=today.format("DD MMMM"))

            channel: TextChannel = self.bot.get_channel(Channels.announcements)
            await channel.send(embed=embed)

        log.debug("Finished fetching birthdays")

    async def fetch_holidays(self, today: Arrow) -> None:
        """Fetches holidays and sending embed if today is a special holiday."""
        today_str = today.format("DD-MM")
        log.debug(f"Fetching birthdays with {today_str}")

        h_file = EVENTS_DIR / "holidays.yml"
        holidays: dict = yaml.load(h_file.open(encoding="UTF-8"), Loader=yaml.FullLoader)

        for holiday in holidays.values():

            if holiday["date"] != today_str:
                continue

            name: str = holiday["name"]
            desc: str = holiday["desc"]
            color: str = holiday["color"]
            emoji: str = holiday["emoji"]

            log.trace(f"Found holiday: {name}. Builing embed.")

            embed = Embed(
                title=f":{emoji}: {name}",
                description=desc,
                colour=color
            )

            embed.set_footer(text=today.format("DD MMMM"))

            channel: TextChannel = self.bot.get_channel(Channels.announcements)

            await channel.send(embed=embed)

        log.debug("Finished fetching holidays")

    @command()
    async def manual_check_events(self, ctx: Context):
        await self.check_day()

    async def cog_check(self, ctx: Context) -> bool:
        """Only allow owners to invoke the commands in this cog."""
        return await commands.is_owner().predicate(ctx)


def setup(bot: IncarnBot) -> None:
    bot.add_cog(Events(bot))
