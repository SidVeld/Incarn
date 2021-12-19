import aiohttp

import incarn
from incarn import constants
from incarn.bot import IncarnBot, StartupError
from incarn.log import get_logger

try:
    incarn.instance = IncarnBot.create_bot()
    incarn.instance.load_extensions()
    incarn.instance.run(constants.Bot.token)
except StartupError as e:
    message = "Unknown StertUp Error Occurred."
    if isinstance(e.exception, (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError)):
        message = "Could not connect to site API. Is it running?"

    log = get_logger("bot")
    log.fatal("", exec_info=e.exception)
    log.fatal(message)
    exit(69)
