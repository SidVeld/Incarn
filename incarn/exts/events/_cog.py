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

        for path, dirs, files in os.walk(events_path):

            for file in files:

                if file.startswith("_") or file.startswith("__"):
                    continue

                file_path = Path(f"{path}/{file}")

                event_data = yaml.load(file_path.open(encoding="utf-8"), Loader=yaml.FullLoader)

                event_date: str = event_data["date"]
                event_date_splitted = event_date.split("-")
                day_month = f"{event_date_splitted[0]}-{event_date_splitted[1]}"
                year = None

                if len(event_date_splitted) == 3:
                    year = int(event_date_splitted[2])

                if day_month != today_str:
                    continue

                embed = Embed()

                if path.endswith("birthdays"):
                    embed.title = f":birthday: Today is the birthday of: {event_data['name']}!"
                    embed.color = 0xec586d

                    embed.add_field(name="Date of birth", value=event_date)

                    if year:
                        embed.add_field(name="Age as of today", value=int(today.format("YYYY")) - year)

                else:
                    embed.title = f":{event_data['emoji']}: {event_data['name']}"
                    embed.color = event_data["color"]

                embed.description = event_data["desc"]

                channel: TextChannel = self.bot.get_channel(Channels.announcements)

                await channel.send(embed=embed)
