import asyncio
import socket
import aiohttp
from contextlib import suppress
from typing import Dict, Optional

import discord
from discord.ext import commands

from incarn import constants
from incarn.log import get_logger

log = get_logger(__name__)


class StartupError(Exception):
    """Exception class for startup errors."""
    def __init__(self, base: Exception):
        super().__init__()
        self.exception = base


class IncarnBot(commands.Bot):
    """Subclass of `discord.ext.commands.Bot`"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.http_session: Optional[aiohttp.ClientSession] = None

        self._connector = None
        self._resolver = None

    @classmethod
    def create_bot(cls) -> "IncarnBot":
        """Create and return an instance of a Bot."""
        loop = asyncio.get_event_loop()
        allowed_roles = list({discord.Object(id_) for id_ in constants.MODERATION_ROLES})

        intents = discord.Intents.all()
        intents.presences = False
        intents.dm_typing = False
        intents.dm_reactions = False
        intents.invites = False
        intents.webhooks = False
        intents.integrations = False

        return cls(
            loop=loop,
            command_prefix=commands.when_mentioned_or(constants.Bot.prefix),
            activity=discord.Game(name=f"Commands: {constants.Bot.prefix}help"),
            case_insensetive=True,
            max_messages=10000,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=allowed_roles),
            intents=intents,
        )

    def load_extensions(self) -> None:
        """Load all enabled extensions."""
        from incarn.utils.extensions import EXTENSIONS

        extensions = set(EXTENSIONS)
        for extension in extensions:
            self.load_extension(extension)

    def add_cog(self, cog: commands.Cog) -> None:
        """Adds a "cog" to the bot and logs the operation."""
        super().add_cog(cog)
        log.info(f"Cog loaded: {cog.qualified_name}")

    def add_command(self, command: commands.Command) -> None:
        """Add `command` as normal and then add its root aliases to the bot."""
        super().add_command(command)
        self._add_root_aliases(command)

    def remove_command(self, name: str) -> Optional[commands.Command]:
        """
        Remove a command/alias as normal and then remove its root aliases from the bot.
        Individual root aliases cannot be removed by this function.
        To remove them, either remove the entire command or manually edit `bot.all_commands`.
        """
        command = super().remove_command(name)
        if command is None:
            # Even if it's a root alias, there's no way to get the Bot instance to remove the alias.
            return

        self._remove_root_aliases(command)
        return command

    def clear(self) -> None:
        """Not implemented! Re-instantiate the bot instead of attempting to re-use a closed one."""
        raise NotImplementedError("Re-using a Bot object after closing it is not supported.")

    async def close(self) -> None:
        """Close the Discord connection and the aiohttp session, connector, statsd client, and resolver."""
        for ext in list(self.extensions):
            with suppress(Exception):
                self.unload_extension(ext)

        for cog in list(self.cogs):
            with suppress(Exception):
                self.remove_cog(cog)

        await super().close()

        if self.http_session:
            await self.http_session.close()

        if self._connector:
            await self._connector.close()

        if self._resolver:
            await self._resolver.close()

    def insert_item_into_filter_list_cache(self, item: Dict[str, str]) -> None:
        """Add an item to the bots filter_list_cache."""
        type_ = item["type"]
        allowed = item["allowed"]
        content = item["content"]

        self.filter_list_cache[f"{type_}.{allowed}"][content] = {
            "id": item["id"],
            "comment": item["comment"],
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }

    async def login(self, *args, **kwargs) -> None:
        self._resolver = aiohttp.AsyncResolver()
        self._connector = aiohttp.TCPConnector(
            resolver=self._resolver,
            family=socket.AF_INET
        )
        self.http.connector = self._connector
        self.http_session = aiohttp.ClientSession(connector=self._connector)
        await super().login(*args, **kwargs)

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Log errors raised in event listeners rather than printing them to stderr."""
        log.exception(f"Unhandled exception in {event}.")

    def _add_root_aliases(self, command: commands.Command) -> None:
        """Recursively add root aliases for `command` and any of its subcommands."""
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                self._add_root_aliases(subcommand)

        for alias in getattr(command, "root_aliases", ()):
            if alias in self.all_commands:
                raise commands.CommandRegistrationError(alias, alias_conflict=True)

            self.all_commands[alias] = command

    def _remove_root_aliases(self, command: commands.Command) -> None:
        """Recursively remove root aliases for `command` and any of its subcommands."""
        if isinstance(command, commands.Group):
            for subcommand in command.commands:
                self._remove_root_aliases(subcommand)

        for alias in getattr(command, "root_aliases", ()):
            self.all_commands.pop(alias, None)
