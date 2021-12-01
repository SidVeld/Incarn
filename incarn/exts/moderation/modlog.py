from datetime import datetime
from typing import Optional, Union, List
from deepdiff import DeepDiff

import discord
from discord import Role
from discord.abc import GuildChannel
from discord.ext.commands import Cog
from discord.ext.commands.context import Context

from incarn import constants
from incarn.bot import IncarnBot
from incarn.constants import Guild as GuildConstant, Channels, Event, Roles, Colours
from incarn.utils.messages import format_user
from incarn.utils.time import discord_timestamp, TimestampFormats

GUILD_CHANNEL = Union[discord.CategoryChannel, discord.TextChannel, discord.VoiceChannel]

CHANNEL_CHANGES_UNSUPPORTED = ("permissions",)
CHANNEL_CHANGES_SUPPRESSED = ("_overwrites", "position")
ROLE_CHANGES_UNSUPPORTED = ("colour", "permissions")


class ModLog(Cog, name="ModLog"):

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot
        self._ignored = {event: [] for event in Event}

        self._cached_deletes = []
        self._cached_edits = []

    def ignore(self, event: Event, *items: int) -> None:
        """Add event to ignored events to suppress log emission."""
        for item in items:
            if item not in self._ignored[event]:
                self._ignored[event].append(item)

    async def send_log_message(
        self,
        title: Optional[str],
        text: str,
        colour: Union[discord.Colour, int],
        icon_url: Optional[str] = None,
        thumbnail: Optional[Union[str, discord.Asset]] = None,
        channel_id: int = Channels.mod_log,
        ping_everyone: bool = False,
        files: Optional[List[discord.File]] = None,
        content: Optional[str] = None,
        additional_embeds: Optional[List[discord.Embed]] = None,
        timestamp_override: Optional[datetime] = None,
        footer: Optional[str] = None,
    ) -> Context:
        """Generate log embed and send to logging channel."""
        # Truncate string directly here to avoid removing newlines
        embed = discord.Embed(
            description=text[:4093] + "..." if len(text) > 4096 else text
        )

        if title and icon_url:
            embed.set_author(name=title, icon_url=icon_url)
        elif title:
            embed.set_author(name=title)

        embed.colour = colour
        embed.timestamp = timestamp_override or datetime.utcnow()

        if footer:
            embed.set_footer(text=footer)

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        if ping_everyone:
            if content:
                content = f"<@&{Roles.moderators}>\n{content}"
            else:
                content = f"<@&{Roles.moderators}>"

        # Truncate content to 2000 characters and append an ellipsis.
        if content and len(content) > 2000:
            content = content[:2000 - 3] + "..."

        channel = self.bot.get_channel(channel_id)
        log_message = await channel.send(
            content=content,
            embed=embed,
            files=files
        )

        if additional_embeds:
            for additional_embed in additional_embeds:
                await channel.send(embed=additional_embed)

        return await self.bot.get_context(log_message)  # Optionally return for use with antispam

    @Cog.listener()
    async def on_guild_role_create(self, role: Role) -> None:
        """Log role create event to mod log."""
        if role.guild.id != GuildConstant.id:
            return

        await self.send_log_message(
            title="Role created",
            text=f"Role id: `{role.id}`",
            colour=Colours.soft_green,
        )

    @Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """Log role delete event to mod log."""
        if role.guild.id != GuildConstant.id:
            return

        await self.send_log_message(
            title="Role deleted",
            text=f"Deleted: **{role.name}** (`{role.id}`)",
            colour=Colours.soft_red,
        )

    @Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role) -> None:
        """Log role update event to mod log."""
        if before.guild.id != GuildConstant.id:
            return

        diff = DeepDiff(before, after)
        changes = []
        done = []

        diff_values = diff.get("values_changed", {})
        diff_values.update(diff.get("type_changes", {}))

        for key, value in diff_values.items():
            if not key:  # Not sure why, but it happens
                continue

            key = key[5:]  # Remove "root." prefix

            if "[" in key:
                key = key.split("[", 1)[0]

            if "." in key:
                key = key.split(".", 1)[0]

            if key in done or key == "color":
                continue

            if key in ROLE_CHANGES_UNSUPPORTED:
                changes.append(f"**{key.title()}** updated")
            else:
                new = value["new_value"]
                old = value["old_value"]

                changes.append(f"**{key.title()}:** `{old}` **→** `{new}`")

            done.append(key)

        if not changes:
            return

        message = ""

        for item in sorted(changes):
            message += f"[ ! ] {item}\n"

        message = f"**{after.name}** (`{after.id}`)\n{message}"

        await self.send_log_message(
            title="Role updated",
            text=message,
            colour=constants.Colours.purple,
        )

    @Cog.listener()
    async def on_guild_channel_create(self, channel: GUILD_CHANNEL) -> None:
        """Log channel create event to mod log."""
        if channel.guild.id != GuildConstant.id:
            return

        if isinstance(channel, discord.CategoryChannel):
            title = "Category created"
            message = f"{channel.name} (`{channel.id}`)"
        elif isinstance(channel, discord.VoiceChannel):
            title = "Voice channel created"

            if channel.category:
                message = f"{channel.category}/{channel.name} (`{channel.id}`)"
            else:
                message = f"{channel.name} (`{channel.id}`)"
        else:
            title = "Text channel created"

            if channel.category:
                message = f"{channel.category}/{channel.name} (`{channel.id}`)"
            else:
                message = f"{channel.name} (`{channel.id}`)"

        await self.send_log_message(
            title=title,
            text=message,
            colour=Colours.soft_green,
        )

    @Cog.listener()
    async def on_guild_channel_delete(self, channel: GUILD_CHANNEL) -> None:
        """Log channel delete event to mod log."""
        if channel.guild.id != GuildConstant.id:
            return

        if isinstance(channel, discord.CategoryChannel):
            title = "Category deleted"
        elif isinstance(channel, discord.VoiceChannel):
            title = "Voice channel deleted"
        else:
            title = "Text channel deleted"

        if channel.category and not isinstance(channel, discord.CategoryChannel):
            message = f"{channel.category}/{channel.name} (`{channel.id}`)"
        else:
            message = f"{channel.name} (`{channel.id}`)"

        await self.send_log_message(
            title=title,
            text=message,
            colour=Colours.soft_red,
        )

    @Cog.listener()
    async def on_guild_channel_update(self, before: GUILD_CHANNEL, after: GuildChannel) -> None:
        """Log channel update event to mod log."""
        if before.guild.id != GuildConstant.id:
            return

        if before.id in self._ignored[Event.guild_channel_update]:
            self._ignored[Event.guild_channel_update].remove(before.id)
            return

        diff = DeepDiff(before, after)
        changes = []
        done = []

        diff_values = diff.get("values_changed", {})
        diff_values.update(diff.get("type_changes", {}))

        for key, value in diff_values.items():
            if not key:  # Not sure why, but it happens
                continue

            key = key[5:]  # Remove "root." prefix

            if "[" in key:
                key = key.split("[", 1)[0]

            if "." in key:
                key = key.split(".", 1)[0]

            if key in done or key in CHANNEL_CHANGES_SUPPRESSED:
                continue

            if key in CHANNEL_CHANGES_UNSUPPORTED:
                changes.append(f"**{key.title()}** updated")
            else:
                new = value["new_value"]
                old = value["old_value"]

                # Discord does not treat consecutive backticks ("``") as an empty inline code block, so the markdown
                # formatting is broken when `new` and/or `old` are empty values. "None" is used for these cases so
                # formatting is preserved.
                changes.append(f"**{key.title()}:** `{old or 'None'}` **→** `{new or 'None'}`")

            done.append(key)

        if not changes:
            return

        message = ""

        for item in sorted(changes):
            message += f"=> {item}\n"

        if after.category:
            message = f"**{after.category}/#{after.name} (`{after.id}`)**\n{message}"
        else:
            message = f"**#{after.name}** (`{after.id}`)\n{message}"

        await self.send_log_message(
            title="Channel updated",
            text=message,
            colour=constants.Colours.purple
        )

    @Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, member: discord.Member) -> None:
        """Log ban event to user log."""
        if guild.id != GuildConstant.id:
            return

        if member.id in self._ignored[Event.member_ban]:
            self._ignored[Event.member_ban].remove(member.id)
            return

        await self.send_log_message(
            title="User banned",
            text=format_user(member),
            thumbnail=member.avatar_url,
            colour=Colours.soft_red,
            channel_id=Channels.user_log
        )

    @Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, member: discord.User) -> None:
        """Log member unban event to mod log."""
        if guild.id != GuildConstant.id:
            return

        if member.id in self._ignored[Event.member_unban]:
            self._ignored[Event.member_unban].remove(member.id)
            return

        await self.send_log_message(
            title="Amnesty! - User unbanned",
            text=format_user(member),
            thumbnail=member.avatar_url,
            colour=Colours.soft_green,
            channel_id=Channels.user_log
        )

    @Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Log member join event to user log."""
        if member.guild.id != GuildConstant.id:
            return

        account_age = discord_timestamp(member.created_at, TimestampFormats.RELATIVE)

        message = format_user(member) + "\n\n**Account created:** " + account_age

        await self.send_log_message(
            title="Member joined",
            text=message,
            colour=Colours.soft_green,
            thumbnail=member.avatar_url,
            channel_id=Channels.user_log
        )

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Log member leave event to user log."""
        if member.guild.id != GuildConstant.id:
            return

        if member.id in self._ignored[Event.member_remove]:
            self._ignored[Event.member_remove].remove(member.id)
            return

        await self.send_log_message(
            title="Member left",
            text=format_user(member),
            colour=Colours.soft_red,
            thumbnail=member.avatar_url,
            channel_id=Channels.user_log
        )

    @staticmethod
    def get_role_diff(before: List[discord.Role], after: List[discord.Role]) -> List[str]:
        """Return a list of strings describing the roles added and removed."""
        changes = []
        before_roles = set(before)
        after_roles = set(after)

        for role in (before_roles - after_roles):
            changes.append(f"**Role removed:** {role.name} (`{role.id}`)")

        for role in (after_roles - before_roles):
            changes.append(f"**Role added:** {role.name} (`{role.id}`)")

        return changes

    @Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Log member update event to user log."""
        if before.guild.id != GuildConstant.id:
            return

        if before.id in self._ignored[Event.member_update]:
            self._ignored[Event.member_update].remove(before.id)

        changes = self.get_role_diff(before.roles, after.roles)

        # The regex is a simple way to exclude all sequence and mapping types.
        diff = DeepDiff(before, after, exclude_regex_paths=r".*\[.*")

        # A type change seems to always take precedent over a value change. Furthermore, it will
        # include the value change along with the type change anyway. Therefore, it's OK to
        # "overwrite" values_changed; in practice there will never even be anything to overwrite.
        diff_values = {**diff.get("values_changed", {}), **diff.get("type_changes", {})}

        for attr, value in diff_values.items():
            if not attr:  # Not sure why, but it happens.
                continue

            attr = attr[5:]  # Remove "root." prefix.
            attr = attr.replace("_", " ").replace(".", " ").capitalize()

            new = value.get("new_value")
            old = value.get("old_value")

            changes.append(f"**{attr}:** `{old}` **→** `{new}`")

        if not changes:
            return

        message = ""

        for item in sorted(changes):
            message += f"-> {item}\n"

        message = f"{format_user(after)}\n{message}"

        await self.send_log_message(
            title="Member updated",
            text=message,
            thumbnail=after.avatar_url,
            colour=Colours.orange,
            channel_id=Channels.user_log
        )

    @Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        if before.id != GuildConstant.id:
            return

        diff = DeepDiff(before, after)
        changes = []
        done = []

        diff_values = diff.get("values_changed", {})
        diff_values.update(diff.get("type_changes", {}))

        for key, value in diff_values.items():
            if not key:  # Not sure why, but it happens
                continue

            key = key[5:]  # Remove "root." prefix

            if "[" in key:
                key = key.split("[", 1)[0]

            if "." in key:
                key = key.split(".", 1)[0]

            if key in done:
                continue

            new = value["new_value"]
            old = value["old_value"]

            changes.append(f"**{key.title()}:** `{old}` **→** `{new}`")

            done.append(key)

        if not changes:
            return

        message = ""

        for item in sorted(changes):
            message += f"[ ! ] {item}\n"

        message = f"**{after.name}** (`{after.id}`)\n{message}"

        await self.send_log_message(
            "Guild updated",
            message,
            colour=Colours.purple,
            thumbnail=after.icon.with_static_format("png")
        )


def setup(bot: IncarnBot):
    bot.add_cog(ModLog(bot))
