import os
import arrow
import yaml
from pathlib import Path

from discord import Embed
from discord.channel import TextChannel
from discord.ext import tasks
from discord.ext.commands import Cog

from incarn.bot import IncarnBot
from incarn.constants import Channels
from incarn.log import get_logger
from incarn.utils import scheduling

log = get_logger(__name__)

num_to_month = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}


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
        self.fetch_holidays.stop()

    async def _plan_fetch(self):
        today = arrow.now()
        next_day = today.shift(days=1)
        next_day_midnight = next_day.replace(hour=0, minute=1, second=0, microsecond=0)
        self.scheduler.schedule_at(next_day_midnight, 1, self.start_fetch())

    async def start_fetch(self):
        self.fetch_holidays.start()

    @tasks.loop(hours=24)
    async def fetch_holidays(self):

        log.debug("Fetching days.")

        today = arrow.now()
        today_str = today.format("DD-MM")

        log.debug(f"Getted today string: {today_str}")

        events_path = Path("incarn/resources/events")

        for file in os.listdir(events_path):

            file_path = events_path / file

            if not os.path.isfile(file_path):
                continue

            event_data = yaml.load(file_path.open(encoding="utf-8"), Loader=yaml.FullLoader)

            event_name: str = event_data["name"]
            event_desc: str = event_data["desc"]
            event_date: str = event_data["date"]
            event_color: str = event_data["color"]

            if not event_date == today_str:
                continue
            else:
                log.debug(f"Founded event {event_name} in {file}")

            event_date = event_date.split("-")
            event_date[1] = num_to_month[event_date[1]]
            event_date = " ".join(event_date)

            embed = Embed()
            embed.title = event_name
            embed.description = event_desc
            embed.set_footer(text=event_date)
            embed.color = event_color

            channel: TextChannel = self.bot.get_channel(Channels.announcements)

            await channel.send(embed=embed)
