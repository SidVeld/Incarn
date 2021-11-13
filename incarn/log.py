import logging
import sys
from logging import Logger, handlers
from pathlib import Path
from typing import Optional, cast

import coloredlogs

from incarn import constants

TRACE_LEVEL = 5


class CustomLogger(Logger):
    """Custom logger class."""

    def trace(self, msg: str, *args, **kwargs) -> None:
        if self.isEnabledFor(TRACE_LEVEL):
            self.log(TRACE_LEVEL, msg)


def get_logger(name: Optional[str] = None) -> CustomLogger:
    return cast(CustomLogger, logging.getLogger(name))


def setup_logger() -> None:
    """Set ups loggers."""
    logging.TRACE = TRACE_LEVEL
    logging.addLevelName(TRACE_LEVEL, "TRACE")
    logging.setLoggerClass(CustomLogger)

    format_string = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    time_string = "%d.%m.%Y | %H:%M:%S"
    log_format = logging.Formatter(format_string, time_string)

    log_file = Path("logs", "bot.log")
    log_file.parent.mkdir(exist_ok=True)
    file_handler = handlers.RotatingFileHandler(log_file, maxBytes=5242880, backupCount=5, encoding="utf8")
    file_handler.setFormatter(log_format)

    root_log = get_logger()
    root_log.addHandler(file_handler)

    coloredlogs.DEFAULT_LEVEL_STYLES = {
        **coloredlogs.DEFAULT_LEVEL_STYLES,
        "trace": {"color": 246},
        "critical": {"background": "red"},
        "debug": coloredlogs.DEFAULT_LEVEL_STYLES["info"]
    }
    coloredlogs.DEFAULT_LOG_FORMAT = format_string
    coloredlogs.DEFAULT_DATE_FORMAT = time_string
    coloredlogs.install(level=TRACE_LEVEL, logger=root_log, stream=sys.stdout)

    root_log.setLevel(logging.DEBUG if constants.DEBUG_MODE else logging.INFO)
    get_logger("discord").setLevel(logging.WARNING)
    get_logger("websockets").setLevel(logging.WARNING)
    get_logger("chardet").setLevel(logging.WARNING)
    get_logger("async_rediscache").setLevel(logging.WARNING)
    get_logger("git").setLevel(logging.WARNING)

    # Set back to the default of INFO even if asyncio's debug mode is enabled.
    get_logger("asyncio").setLevel(logging.INFO)

    _set_trace_loggers()


def _set_trace_loggers() -> None:
    """
    Set loggers to the trace level according to the value from the config-file.

    When the env var is a list of logger names delimited by a comma,
    each of the listed loggers will be set to the trace level.

    If this list is prefixed with a "!", all of the loggers except the listed ones will be set to the trace level.

    Otherwise if the env var begins with a "*",
    the root logger is set to the trace level and other contents are ignored.
    """
    level_filter = constants.Bot.trace_loggers
    if level_filter:
        if level_filter.startswith("*"):
            get_logger().setLevel(TRACE_LEVEL)

        elif level_filter.startswith("!"):
            get_logger().setLevel(TRACE_LEVEL)
            for logger_name in level_filter.strip("!,").split(","):
                get_logger(logger_name).setLevel(logging.DEBUG)

        else:
            for logger_name in level_filter.strip(",").split(","):
                get_logger(logger_name).setLevel(TRACE_LEVEL)
