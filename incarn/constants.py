"""
Loads bot configuration from YAML files.
By default, this simply loads the default
configuration located at `config-default.yml`.
If a file called `config.yml` is found in the
project directory, the default configuration
is recursively updated with any settings from
the custom configuration. Any settings left
out in the custom user configuration will stay
their default values from `config-default.yml`.

Original by Python-Discord: https://github.com/python-discord
"""

import os
from collections.abc import Mapping
from enum import Enum
from pathlib import Path
from typing import List, Optional

import yaml


def _join_var_constructor(loader, node):
    """
    Implements a custom YAML tag for concatenating other tags in
    the document to strings. This allows for a much more DRY configuration
    file.
    """

    fields = loader.construct_sequence(node)
    return "".join(str(x) for x in fields)


yaml.SafeLoader.add_constructor("!JOIN", _join_var_constructor)

with open("config.yml", encoding="UTF-8") as f:
    _CONFIG_YAML = yaml.safe_load(f)


def _recursive_update(original, new):
    """
    Helper method which implements a recursive `dict.update`
    method, used for updating the original configuration with
    configuration specified by the user.
    """

    for key, value in original.items():
        if key not in new:
            continue

        if isinstance(value, Mapping):
            if not any(isinstance(subvalue, Mapping) for subvalue in value.values()):
                original[key].update(new[key])
            _recursive_update(original[key], new[key])
        else:
            original[key] = new[key]


if Path("config.yml").exists():
    print("Found config file. Loading.")
    with open("config.yml", encoding="UTF-8") as f:
        user_config = yaml.safe_load(f)
    _recursive_update(_CONFIG_YAML, user_config)


def check_reqired_keys(keys):
    """
    Verifies that keys that are set to be required are present in the
    loaded configuration.
    """

    for key_path in keys:
        lookup = _CONFIG_YAML
        try:
            for key in key_path.split('.'):
                lookup = lookup[key]
                if lookup is None:
                    raise KeyError(key)
        except KeyError:
            raise KeyError(
                f"A configuration for `{key_path}` is required, but not found. "
                "Please set it in config.yml or setup an enviroment variable and try again."
            )


try:
    required_keys = _CONFIG_YAML["config"]["required_keys"]
except KeyError:
    pass
else:
    check_reqired_keys(required_keys)


class YAMLGetter(type):
    """
    Implements a custom metaclass used for accessing
    configuration data by simply accessing class attributes.
    Supports getting configuration from up to two levels
    of nested configuration through `section` and `subsection`.

    `section` specifies the YAML configuration section (or "key")
    in which the configuration lives, and must be set.

    `subsection` is an optional attribute specifying the section
    within the section from which configuration should be loaded.

    Example Usage:
        # config.yml
        bot:
            prefixes:
                direct_message: ''
                guild: '!'
        # config.py
        class Prefixes(metaclass=YAMLGetter):
            section = "bot"
            subsection = "prefixes"
        # Usage in Python code
        from config import Prefixes
        def get_prefix(bot, message):
            if isinstance(message.channel, PrivateChannel):
                return Prefixes.direct_message
            return Prefixes.guild
    """

    subsection = None

    def __getattr__(cls, name: str):
        name = name.lower()

        try:
            if cls.subsection is not None:
                return _CONFIG_YAML[cls.section][cls.subsection][name]
            return _CONFIG_YAML[cls.section][name]
        except KeyError as e:
            dotted_path = ".".join(
                (cls.section, cls.subsection, name)
                if cls.subsection is not None else (cls.section, name)
            )
            print(f"Tried accessing config-var at `{dotted_path}` ,but could not be found.`")
            raise AttributeError(repr(name)) from e

    def __getitem__(cls, name):
        return cls.__getattr__(name)

    def __iter__(cls):
        """Return generator of key: value pairs of currents class' config values."""
        for name in cls.__annotations__:
            yield name, getattr(cls, name)


class Bot(metaclass=YAMLGetter):
    section = "bot"

    prefix: str
    token: str
    trace_loggers: Optional[str]
    owners: list


class Colours(metaclass=YAMLGetter):
    section = "style"
    subsection = "colours"

    blue: int
    bright_green: int
    orange: int
    pink: int
    purple: int
    soft_green: int
    soft_orange: int
    soft_red: int
    white: int
    yellow: int


class Emojis(metaclass=YAMLGetter):
    section = "style"
    subsection = "emojis"

    trashcan: str


class Categories(metaclass=YAMLGetter):
    section = "guild"
    subsection = "categories"

    admins: int
    modeators: int
    voice: int


class Channels(metaclass=YAMLGetter):
    section = "guild"
    subsection = "channels"

    announcements: int

    admins: int
    admins_spam: int
    moderators: int
    bot_commands: int

    mod_log: int
    user_log: int
    message_log: int
    voice_log: int

    voice_chat_0: int
    voice_chat_1: int
    voice_chat_afk: int


class Roles(metaclass=YAMLGetter):
    section = "guild"
    subsection = "roles"

    owners: int
    admins: int
    moderators: int
    mod_team: int
    regular: int
    bots: int


class Guild(metaclass=YAMLGetter):
    section = "guild"

    id: int
    invite: str

    moderation_categories: List[int]
    moderation_channels: List[int]
    modlog_blacklist: List[int]
    reminder_whitelist: List[int]
    moderation_roles: List[int]
    staff_roles: List[int]


class RedirectOutput(metaclass=YAMLGetter):
    section = 'redirect_output'

    delete_delay: int
    delete_invocation: bool


class URLs(metaclass=YAMLGetter):
    section = "urls"

    discord_api: str
    discord_invite_api: str

    github_bot_repo: str


class Event(Enum):
    """
    Event names. This does not include every event (for example, raw
    events aren't here), but only events used in ModLog for now.
    """

    guild_channel_create = "guild_channel_create"
    guild_channel_delete = "guild_channel_delete"
    guild_channel_update = "guild_channel_update"
    guild_role_create = "guild_role_create"
    guild_role_delete = "guild_role_delete"
    guild_role_update = "guild_role_update"
    guild_update = "guild_update"

    member_join = "member_join"
    member_remove = "member_remove"
    member_ban = "member_ban"
    member_unban = "member_unban"
    member_update = "member_update"

    message_delete = "message_delete"
    message_edit = "message_edit"

    voice_state_update = "voice_state_update"


# Debug mode
DEBUG_MODE: bool = _CONFIG_YAML["debug"] == "true"

# Paths
BOT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BOT_DIR, os.pardir))

# Default role combinations
MODERATION_ROLES = Guild.moderation_roles
STAFF_ROLES = Guild.staff_roles

# Channel combinations
MODERATION_CHANNELS = Guild.moderation_channels

# Category combinations
MODERATION_CATEGORIES = Guild.moderation_categories


# Bot replies
NEGATIVE_REPLIES = [
    "No.",
    "No!",
    "Nope.",
    "Nah.",
    "Rejected.",
    "NOT.",
    "Not today.",
    "No way.",
    "Negative.",
    "ABSOLUTLEY NO.",
]

POSITIVE_REPLIES = [
    "Yes!",
    "Yep!",
    "Sure!",
    "Alright!"
    "Yep.",
    "Absolutely!",
    "Can do!",
    "Affirmative!",
]

ERROR_REPLIES = [
    "Error!",
    "Stop! Error!",
    "Heuston, we have a problem",
    "Er-r-r-rro-r-r.",
    "Stop it!",
    "Sheer Heart Attack",
    "DAMN!",
    "Woops, we fucked up!",
]
