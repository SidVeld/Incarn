
import colorsys
import rapidfuzz
import textwrap
from collections import defaultdict
from typing import DefaultDict, Optional, Union

from discord import Colour, Embed, Guild, Message, Role
from discord.channel import DMChannel
from discord.ext.commands import Cog, Context, command, has_any_role
from discord.ext.commands.core import guild_only
from discord.utils import escape_markdown

from incarn import constants
from incarn.bot import IncarnBot
from incarn.converters import MemberOrUser
from incarn.errors import NonExistentRoleError
from incarn.log import get_logger
from incarn.pagination import LinePaginator
from incarn.utils.channel import is_staff_channel
from incarn.utils.members import get_or_fetch_member
from incarn.utils.time import TimestampFormats, discord_timestamp

log = get_logger(__name__)


class Information(Cog):
    """A cog with commands for generating embeds with server info, such as server stats and user info."""

    def __init__(self, bot: IncarnBot):
        self.bot = bot

    @staticmethod
    def get_channel_type_counts(guild: Guild) -> DefaultDict[str, int]:
        """Return the total amounts of the various types of channels in `guild`."""
        channel_counter = defaultdict(int)

        for channel in guild.channels:
            if is_staff_channel(channel):
                channel_counter["staff"] += 1
            else:
                channel_counter[str(channel.type)] += 1

        return channel_counter

    @staticmethod
    def join_role_stats(role_ids: list[int], guild: Guild, name: Optional[str] = None) -> dict[str, int]:
        """Return a dictionary with the number of `members` of each role given, and the `name` for this joined group."""
        member_count = 0
        for role_id in role_ids:
            if (role := guild.get_role(role_id)) is not None:
                member_count += len(role.members)
            else:
                raise NonExistentRoleError(role_id)
        return {name or role.name.title(): member_count}

    @staticmethod
    def get_member_counts(guild: Guild) -> dict[str, int]:
        """Return the total number of members for certain roles in `guild`."""
        role_ids = [
            constants.Roles.admins, constants.Roles.moderators,
            constants.Roles.regular, constants.Roles.bots
        ]

        role_stats = {}
        for role_id in role_ids:
            role_stats.update(Information.join_role_stats([role_id], guild))
        return role_stats

    @guild_only()
    @has_any_role(*constants.MODERATION_ROLES)
    @command(name="roles")
    async def roles_info(self, ctx: Context) -> None:
        """Returns a list of all roles and their corresponding IDs."""
        # Sort the roles alphabetically and remove the @everyone role
        roles = sorted(ctx.guild.roles[1:], key=lambda role: role.name)

        # Build a list
        role_list = []
        for role in roles:
            role_list.append(f"`{role.id}` - {role.mention}")

        # Build an embed
        embed = Embed(
            title=f"Role information (Total {len(roles)} role{'s' * (len(role_list) > 1)})"
        )

        await LinePaginator.paginate(role_list, ctx, embed, empty=False)

    @guild_only()
    @has_any_role(*constants.MODERATION_ROLES)
    @command(name="role")
    async def role_info(self, ctx: Context, *roles: Union[Role, str]) -> None:
        """
        Return information on a role or list of roles.

        To specify multiple roles just add to the arguments, delimit roles with spaces in them using quotation marks.
        """
        parsed_roles = set()
        failed_roles = set()

        all_roles = {role.id: role.name for role in ctx.guild.roles}
        for role_name in roles:
            if isinstance(role_name, Role):
                # Role conversion has already succeeded
                parsed_roles.add(role_name)
                continue

            match = rapidfuzz.process.extractOne(
                role_name, all_roles, score_cutoff=80,
                scorer=rapidfuzz.fuzz.ratio
            )

            if not match:
                failed_roles.add(role_name)
                continue

            # `match` is a (role name, score, role id) tuple
            role = ctx.guild.get_role(match[2])
            parsed_roles.add(role)

        if failed_roles:
            await ctx.send(f":x: Could not retrieve the following roles: {', '.join(failed_roles)}")

        for role in parsed_roles:
            h, s, v = colorsys.rgb_to_hsv(*role.colour.to_rgb())

            embed = Embed(
                title=f"{role.name} info",
                colour=role.colour,
            )
            embed.add_field(name="ID", value=role.id, inline=True)
            embed.add_field(name="Colour (RGB)", value=f"#{role.colour.value:0>6x}", inline=True)
            embed.add_field(name="Colour (HSV)", value=f"{h:.2f} {s:.2f} {v}", inline=True)
            embed.add_field(name="Member count", value=len(role.members), inline=True)
            embed.add_field(name="Position", value=role.position)
            embed.add_field(name="Permission code", value=role.permissions.value, inline=True)

            await ctx.send(embed=embed)

    @guild_only()
    @command(name="server", aliases=["server_info", "guild", "guild_info"])
    async def server_info(self, ctx: Context) -> None:
        """Returns an embed full of server information."""
        embed = Embed(title="Server Information")

        created = discord_timestamp(ctx.guild.created_at, TimestampFormats.RELATIVE)
        num_roles = len(ctx.guild.roles) - 1  # Exclude @everyone

        # Server Features are only useful in certain channels
        if ctx.channel.id in (
            *constants.MODERATION_CHANNELS,
        ):
            features = f"\nFeatures: {', '.join(ctx.guild.features)}"
        else:
            features = ""

        total_members = f"{ctx.guild.member_count:,}"
        total_channels = len(ctx.guild.channels)

        embed.description = (
            f"Created: {created}"
            f"{features}"
            f"\nRoles: {num_roles}"
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)

        if ctx.guild.id == constants.Guild.id:

            # Members
            member_counts = self.get_member_counts(ctx.guild)
            member_info = "\n".join(f"{role}: {count}" for role, count in member_counts.items())
            embed.add_field(name=f"Members: {total_members}", value=member_info)

            # Channels
            channel_counts = self.get_channel_type_counts(ctx.guild)
            channel_info = "\n".join(
                f"{channel.title()}: {count}" for channel, count in sorted(channel_counts.items())
            )
            embed.add_field(name=f"Channels: {total_channels}", value=channel_info)

        else:
            embed.description += (
                f"\nMembers: {total_members}"
                f"\nChannels: {total_channels}"
            )

        await ctx.send(embed=embed)

    async def create_user_embed(self, ctx: Context, user: MemberOrUser) -> Embed:
        """Creates an embed containing information on the `user`."""

        invoked_in_dm = isinstance(ctx.channel, DMChannel)

        name = str(user)
        created = discord_timestamp(user.created_at, TimestampFormats.RELATIVE)

        fields = [
            (
                "User information",
                textwrap.dedent(f"""
                    Created: {created}
                    Profile: {user.mention}
                    ID: {user.id}
                """).strip()
            )
        ]

        if invoked_in_dm is False:
            on_server = bool(await get_or_fetch_member(ctx.guild, user.id))

            if on_server and user.nick:
                name = f"{user.nick} ({name})"

            if on_server:
                if user.joined_at:
                    joined = discord_timestamp(user.joined_at, TimestampFormats.RELATIVE)
                else:
                    joined = "Unable to get join date"

                # The 0 is for excluding the default @everyone role,
                # and the -1 is for reversing the order of the roles to highest to lowest in hierarchy.
                roles_list = user.roles[:0:-1]

                roles = ", ".join(role.mention for role in roles_list[:20])

                if len(roles_list) - 20 > 0:
                    roles += " and more."

                membership = {"Joined": joined, "Roles": roles or None}

                membership = textwrap.dedent("\n".join([f"{key}: {value}" for key, value in membership.items()]))
            else:
                roles = None
                membership = "The user is not a member of the server"

            fields.append(("Member information", membership))

        name = escape_markdown(name)

        embed = Embed(title=name)

        for field_name, field_content in fields:
            embed.add_field(name=field_name, value=field_content, inline=False)

        embed.set_thumbnail(url=user.avatar_url)

        if user.colour != Colour.default():
            embed.colour = user.colour

        return embed

    @command(name="whoami", aliases=("me", "aboutme"))
    async def whoami(self, ctx: Context):
        embed = await self.create_user_embed(ctx, ctx.author)
        await ctx.send(embed=embed)

    @command(name="whois", aliases=("user", "user_info", "member", "member_info", "u"))
    async def whois(self, ctx: Context, user_or_message: Union[MemberOrUser, Message] = None) -> None:
        """Returns info about a user."""
        if isinstance(user_or_message, Message):
            user = user_or_message.author
        else:
            user = user_or_message

        if user is None:
            user = ctx.author

        embed = await self.create_user_embed(ctx, user)
        await ctx.send(embed=embed)

    @command(name="avatar")
    async def avatar(self, ctx: Context, user_or_message: Union[MemberOrUser, Message] = None) -> None:
        if isinstance(user_or_message, Message):
            user = user_or_message.author
        else:
            user = user_or_message

        if user is None:
            user = ctx.author

        embed = Embed(title=f"Avatar: {user}")
        embed.set_image(url=user.avatar_url)

        await ctx.send(embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(Information(bot))
