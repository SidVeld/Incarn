from __future__ import annotations

import re
import typing as t
from datetime import datetime, timezone
from ssl import CertificateError

import dateutil.parser
import dateutil.tz
import discord
from aiohttp import ClientConnectorError
from dateutil.relativedelta import relativedelta
from discord.ext.commands import BadArgument, Context, Converter, IDConverter, MemberConverter, UserConverter
from discord.utils import snowflake_time, escape_markdown

from incarn import exts
from incarn.constants import URLs
from incarn.log import get_logger
from incarn.utils.extensions import EXTENSIONS, unqualify
from incarn.utils.regex import INVITE_RE
from incarn.utils.time import parse_duration_string

if t.TYPE_CHECKING:
    from incarn.exts.info.source import SourceType

log = get_logger(__name__)

DISCORD_EPOCH_DT = snowflake_time(0)
RE_USER_MENTION = re.compile(r"<@!?([0-9]+)>$")


def allowed_strings(*values, preserve_case: bool = False) -> t.Callable[[str], str]:
    """
    Return a converter which only allows arguments equal to one of the given values.
    Unless preserve_case is True, the argument is converted to lowercase. All values are then
    expected to have already been given in lowercase too.
    """
    def converter(arg: str) -> str:
        if not preserve_case:
            arg = arg.lower()

        if arg not in values:
            raise BadArgument(f"Only the following values are allowed:\n```{', '.join(values)}```")
        else:
            return arg

    return converter


class ValidDiscordServerInvite(Converter):
    """
    A converter that validates whether a given string is a valid Discord server invite.

    Raises 'BadArgument' if:
    - The string is not a valid Discord server invite.
    - The string is valid, but is an invite for a group DM.
    - The string is valid, but is expired.

    Returns a (partial) guild object if:
    - The string is a valid vanity
    - The string is a full invite URI
    - The string contains the invite code (the stuff after discord.gg/)

    See the Discord API docs for documentation on the guild object:
    https://discord.com/developers/docs/resources/guild#guild-object
    """

    async def convert(self, ctx: Context, server_invite: str) -> dict:
        """Check whether the string is a valid Discord server invite."""
        invite_code = INVITE_RE.match(server_invite)
        if invite_code:
            response = await ctx.bot.http_session.get(
                f"{URLs.discord_invite_api}/{invite_code.group('invite')}"
            )
            if response.status != 404:
                invite_data = await response.json()
                return invite_data.get("guild")

        id_converter = IDConverter()
        if id_converter._get_id_match(server_invite):
            raise BadArgument("Guild IDs are not supported, only invites.")

        raise BadArgument("This does not appear to be a valid Discord server invite.")


class Extension(Converter):
    """
    Fully qualify the name of an extension and ensure it exists.
    The * and ** values bypass this when used with the reload command.
    """

    async def convert(self, ctx: Context, argument: str) -> str:
        """Fully qualify the name of an extension and ensure it exists."""
        # Special values to reload all extensions
        if argument == "*" or argument == "**":
            return argument

        argument = argument.lower()

        if argument in EXTENSIONS:
            return argument
        elif (qualified_arg := f"{exts.__name__}.{argument}") in EXTENSIONS:
            return qualified_arg

        matches = []
        for ext in EXTENSIONS:
            if argument == unqualify(ext):
                matches.append(ext)

        if len(matches) > 1:
            matches.sort()
            names = "\n".join(matches)
            raise BadArgument(
                f":x: `{argument}` is an ambiguous extension name. "
                f"Please use one of the following fully-qualified names.```\n{names}```"
            )
        elif matches:
            return matches[0]
        else:
            raise BadArgument(f":x: Could not find the extension `{argument}`.")


class PackageName(Converter):
    """
    A converter that checks whether the given string is a valid package name.
    Package names are used for stats and are restricted to the a-z and _ characters.
    """

    PACKAGE_NAME_RE = re.compile(r"[^a-z0-9_]")

    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> str:
        """Checks whether the given string is a valid package name."""
        if cls.PACKAGE_NAME_RE.search(argument):
            raise BadArgument("The provided package name is not valid; please only use the _, 0-9, and a-z characters.")
        return argument


class ValidURL(Converter):
    """
    Represents a valid webpage URL.
    This converter checks whether the given URL can be reached and requesting it returns a status
    code of 200. If not, `BadArgument` is raised.
    Otherwise, it simply passes through the given URL.
    """

    @staticmethod
    async def convert(ctx: Context, url: str) -> str:
        """This converter checks whether the given URL can be reached with a status code of 200."""
        try:
            async with ctx.bot.http_session.get(url) as resp:
                if resp.status != 200:
                    raise BadArgument(
                        f"HTTP GET on `{url}` returned status `{resp.status}`, expected 200"
                    )
        except CertificateError:
            if url.startswith('https'):
                raise BadArgument(
                    f"Got a `CertificateError` for URL `{url}`. Does it support HTTPS?"
                )
            raise BadArgument(f"Got a `CertificateError` for URL `{url}`.")
        except ValueError:
            raise BadArgument(f"`{url}` doesn't look like a valid hostname to me.")
        except ClientConnectorError:
            raise BadArgument(f"Cannot connect to host with URL `{url}`.")
        return url


class TagNameConverter(Converter):
    """
    Ensure that a proposed tag name is valid.
    Valid tag names meet the following conditions:
        * All ASCII characters
        * Has at least one non-whitespace character
        * Not solely numeric
        * Shorter than 127 characters
    """

    @staticmethod
    async def convert(ctx: Context, tag_name: str) -> str:
        """Lowercase & strip whitespace from proposed tag_name & ensure it's valid."""
        tag_name = tag_name.lower().strip()

        # The tag name has at least one invalid character.
        if ascii(tag_name)[1:-1] != tag_name:
            raise BadArgument("Don't be ridiculous, you can't use that character!")

        # The tag name is either empty, or consists of nothing but whitespace.
        elif not tag_name:
            raise BadArgument("Tag names should not be empty, or filled with whitespace.")

        # The tag name is longer than 127 characters.
        elif len(tag_name) > 127:
            raise BadArgument("Are you insane? That's way too long!")

        # The tag name is ascii but does not contain any letters.
        elif not any(character.isalpha() for character in tag_name):
            raise BadArgument("Tag names must contain at least one letter.")

        return tag_name


class SourceConverter(Converter):
    """Convert an argument into a help command, tag, command, or cog."""

    @staticmethod
    async def convert(ctx: Context, argument: str) -> SourceType:
        """Convert argument into source object."""
        if argument.lower() == "help":
            return ctx.bot.help_command

        cog = ctx.bot.get_cog(argument)
        if cog:
            return cog

        cmd = ctx.bot.get_command(argument)
        if cmd:
            return cmd

        tags_cog = ctx.bot.get_cog("Tags")
        show_tag = True

        if not tags_cog:
            show_tag = False
        elif argument.lower() in tags_cog._cache:
            return argument.lower()

        escaped_arg = escape_markdown(argument)

        raise BadArgument(
            f"Unable to convert '{escaped_arg}' to valid command{', tag,' if show_tag else ''} or Cog."
        )


class DurationDelta(Converter):
    """Convert duration strings into dateutil.relativedelta.relativedelta objects."""

    async def convert(self, ctx: Context, duration: str) -> relativedelta:
        """
        Converts a `duration` string to a relativedelta object.
        The converter supports the following symbols for each unit of time:
        - years: `Y`, `y`, `year`, `years`
        - months: `m`, `month`, `months`
        - weeks: `w`, `W`, `week`, `weeks`
        - days: `d`, `D`, `day`, `days`
        - hours: `H`, `h`, `hour`, `hours`
        - minutes: `M`, `minute`, `minutes`
        - seconds: `S`, `s`, `second`, `seconds`
        The units need to be provided in descending order of magnitude.
        """
        if not (delta := parse_duration_string(duration)):
            raise BadArgument(f"`{duration}` is not a valid duration string.")

        return delta


class Duration(DurationDelta):
    """Convert duration strings into UTC datetime.datetime objects."""

    async def convert(self, ctx: Context, duration: str) -> datetime:
        """
        Converts a `duration` string to a datetime object that's `duration` in the future.

        The converter supports the same symbols for each unit of time as its parent class.
        """
        delta = await super().convert(ctx, duration)
        now = datetime.now(timezone.utc)

        try:
            return now + delta
        except (ValueError, OverflowError):
            raise BadArgument(f"`{duration}` results in a datetime outside the supported range.")


class Age(DurationDelta):
    """Convert duration strings into UTC datetime.datetime objects."""

    async def convert(self, ctx: Context, duration: str) -> datetime:
        """
        Converts a `duration` string to a datetime object that's `duration` in the past.
        The converter supports the same symbols for each unit of time as its parent class.
        """
        delta = await super().convert(ctx, duration)
        now = datetime.now(timezone.utc)

        try:
            return now - delta
        except (ValueError, OverflowError):
            raise BadArgument(f"`{duration}` results in a datetime outside the supported range.")


class ISODateTime(Converter):
    """Converts an ISO-8601 datetime string into a datetime.datetime."""

    async def convert(self, ctx: Context, datetime_string: str) -> datetime:
        """
        Converts a ISO-8601 `datetime_string` into a `datetime.datetime` object.
        The converter is flexible in the formats it accepts, as it uses the `isoparse` method of
        `dateutil.parser`. In general, it accepts datetime strings that start with a date,
        optionally followed by a time. Specifying a timezone offset in the datetime string is
        supported, but the `datetime` object will be converted to UTC. If no timezone is specified, the datetime will
        be assumed to be in UTC already. In all cases, the returned object will have the UTC timezone.

        See: https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.isoparse

        Formats that are guaranteed to be valid by our tests are:
        - `YYYY-mm-ddTHH:MM:SSZ` | `YYYY-mm-dd HH:MM:SSZ`
        - `YYYY-mm-ddTHH:MM:SS±HH:MM` | `YYYY-mm-dd HH:MM:SS±HH:MM`
        - `YYYY-mm-ddTHH:MM:SS±HHMM` | `YYYY-mm-dd HH:MM:SS±HHMM`
        - `YYYY-mm-ddTHH:MM:SS±HH` | `YYYY-mm-dd HH:MM:SS±HH`
        - `YYYY-mm-ddTHH:MM:SS` | `YYYY-mm-dd HH:MM:SS`
        - `YYYY-mm-ddTHH:MM` | `YYYY-mm-dd HH:MM`
        - `YYYY-mm-dd`
        - `YYYY-mm`
        - `YYYY`

        Note: ISO-8601 specifies a `T` as the separator between the date and the time part of the
        datetime string. The converter accepts both a `T` and a single space character.
        """
        try:
            dt = dateutil.parser.isoparse(datetime_string)
        except ValueError:
            raise BadArgument(f"`{datetime_string}` is not a valid ISO-8601 datetime string")

        if dt.tzinfo:
            dt = dt.astimezone(dateutil.tz.UTC)
        else:  # Without a timezone, assume it represents UTC.
            dt = dt.replace(tzinfo=dateutil.tz.UTC)

        return dt


class HushDurationConverter(Converter):
    """Convert passed duration to `int` minutes or `None`."""

    MINUTES_RE = re.compile(r"(\d+)(?:M|m|$)")

    async def convert(self, ctx: Context, argument: str) -> int:
        """
        Convert `argument` to a duration that's max 15 minutes or None.

        If `"forever"` is passed, -1 is returned; otherwise an int of the extracted time.

        Accepted formats are:
        * <duration>,
        * <duration>m,
        * <duration>M,
        * forever.
        """
        if argument == "forever":
            return -1
        match = self.MINUTES_RE.match(argument)
        if not match:
            raise BadArgument(f"{argument} is not a valid minutes duration.")

        duration = int(match.group(1))
        if duration > 15:
            raise BadArgument("Duration must be at most 15 minutes.")
        return duration


def _is_an_unambiguous_user_argument(argument: str) -> bool:
    """Check if the provided argument is a user mention, user id, or username (name#discrim)."""
    has_id_or_mention = bool(IDConverter()._get_id_match(argument) or RE_USER_MENTION.match(argument))

    # Check to see if the author passed a username (a discriminator exists)
    argument = argument.removeprefix('@')
    has_username = len(argument) > 5 and argument[-5] == '#'

    return has_id_or_mention or has_username


AMBIGUOUS_ARGUMENT_MSG = ("`{argument}` is not a User mention, a User ID or a Username in the format"
                          " `name#discriminator`.")


class UnambiguousUser(UserConverter):
    """
    Converts to a `discord.User`, but only if a mention, userID or a username (name#discrim) is provided.

    Unlike the default `UserConverter`, it doesn't allow conversion from a name.

    This is useful in cases where that lookup strategy would lead to too much ambiguity.
    """

    async def convert(self, ctx: Context, argument: str) -> discord.User:
        """Convert the `argument` to a `discord.User`."""
        if _is_an_unambiguous_user_argument(argument):
            return await super().convert(ctx, argument)
        else:
            raise BadArgument(AMBIGUOUS_ARGUMENT_MSG.format(argument=argument))


class UnambiguousMember(MemberConverter):
    """
    Converts to a `discord.Member`, but only if a mention, userID or a username (name#discrim) is provided.

    Unlike the default `MemberConverter`, it doesn't allow conversion from a name or nickname.

    This is useful in cases where that lookup strategy would lead to too much ambiguity.
    """

    async def convert(self, ctx: Context, argument: str) -> discord.Member:
        """Convert the `argument` to a `discord.Member`."""
        if _is_an_unambiguous_user_argument(argument):
            return await super().convert(ctx, argument)
        else:
            raise BadArgument(AMBIGUOUS_ARGUMENT_MSG.format(argument=argument))


Expiry = t.Union[Duration, ISODateTime]
MemberOrUser = t.Union[discord.Member, discord.User]
UnambiguousMemberOrUser = t.Union[UnambiguousMember, UnambiguousUser]
