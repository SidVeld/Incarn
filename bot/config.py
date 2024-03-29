import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .classes.exceptions import InconvertibleVariableError


def get_bool(env_value: str) -> bool:
    """
    Converts the type of the received environment variable to bool.

    The variable must be either `True` or `False`.
    Otherwise, an error will appear.

    :param str env_value: The value of the environment variable to be converted. Case-insensitive.
    :return: Value of environment variable of `bool` type.
    :raises InconvertibleVariableError: A variable cannot be converted to a `bool`.
    """
    match env_value.lower():
        case "true":
            return True
        case "false":
            return False
        case _:
            message = f"Cannot convert '{env_value}' to True or False."
            raise InconvertibleVariableError(message)


def get_list(env_value: str) -> list[int]:
    """
    Converts the type of the received environment variable to list of integers.

    :param str env_value: The value of the environment variable to be converted.
    :return: Value of environment variable of `list` type.
    """
    return [int(item.strip()) for item in env_value.split(",")]


@dataclass
class ClientConfig:
    prefix: str
    token: str
    owners: list[int]
    sync_commands: bool


@dataclass
class DebugConfig:
    enabled: bool
    debug_orm: bool
    guilds: list[int]


@dataclass
class DatabaseConfig:
    host: str
    port: str
    username: str
    password: str
    database: str


load_dotenv()


CLIENT_CONFIG = ClientConfig(
    os.getenv("BOT_PREFIX"),
    os.getenv("BOT_TOKEN"),
    get_list(os.getenv("BOT_OWNERS")),
    get_bool(os.getenv("BOT_SYNC_COMMANDS")),
)


DEBUG_CONFIG = DebugConfig(
    get_bool(os.getenv("DEBUG_ENABLED")),
    get_bool(os.getenv("DEBUG_ORM")),
    get_list(os.getenv("DEBUG_GUILDS"))
)


DATABASE_CONFIG = DatabaseConfig(
    os.getenv("POSTGRES_HOST"),
    os.getenv("POSTGRES_PORT"),
    os.getenv("POSTGRES_USER"),
    os.getenv("POSTGRES_PASSWORD"),
    os.getenv("POSTGRES_DB"),
)
