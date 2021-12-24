import os
import yaml
from pathlib import Path
from typing import Optional

from discord import Embed
from discord.ext.commands import Cog, Context, group
from discord.guild import Guild

from incarn.bot import IncarnBot


class HomeRules(Cog):
    """Commands for managing server's homerules."""

    @group(name="homerules", aliases=("hmrls", "hmrules"))
    async def homerules_command(self, ctx: Context):
        """Commands for managing server's homerules."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot

        if not Path("incarn/resources/guilds/").exists():
            os.makedirs("incarn/resources/guilds/")

        self.path_to_guilds = Path("incarn/resources/guilds/")

    def get_guild_dir(self, guild: Guild) -> Path:
        """Returning guild's directory."""

        path_to_dir = self.path_to_guilds / str(guild.id)

        if not path_to_dir.exists():
            os.makedirs(path_to_dir)

        return path_to_dir

    def get_homerules_file(self, guild: Guild):
        """Returning guild's homerules file."""
        return self.get_guild_dir(guild) / "homerules.yml"

    def get_homerules_data(self, guild: Guild) -> Optional[dict]:
        """Returning data from guild's homerules file."""
        file = self.get_homerules_file(guild)
        try:
            data: dict = yaml.load(file.open(encoding="UTF-8"), Loader=yaml.FullLoader)
            return data
        except FileNotFoundError:
            return None

    def dump_data(self, guild, data) -> None:
        """Dumping new data to guild's homerules file."""
        file = self.get_homerules_file(guild).open(mode="w", encoding="utf-8")
        yaml.dump(data, file, allow_unicode=True)

    @homerules_command.command(name="initialize", aliases=("init", "Initialize"))
    async def homerules_initialize(self, ctx: Context, homerules_count: int = 5) -> None:
        """
        Initialize homerules for this server.
        """

        if self.get_homerules_file(ctx.guild).exists():
            await ctx.send("This server has already initialized the homerules.")
            return

        homerules = {}
        for index in range(homerules_count):
            homerules[index + 1] = "Blank rule."

        data = {
            "title": None,
            "desc": None,
            "rule_name_override": None,
            "rules": homerules,
            "footer": None
        }

        self.dump_data(ctx.guild, data)

        await ctx.send("Homerules initialized.")

    @homerules_command.command(name="show")
    async def homerules_show(self, ctx: Context) -> None:
        """
        Sends message with homerules of this server.
        """

        data = self.get_homerules_data(ctx.guild)

        if data is None:
            await ctx.send("There is no rules!")
            return

        embed = Embed()

        if data["title"] is not None:
            embed.title = data["title"]
        else:
            embed.title = "Homerules"

        if data["desc"] is not None:
            embed.description = data["desc"]
        else:
            embed.description = "The following homerules apply:"

        if data["rulename"] is not None:
            rule_name = data["rulename"]
        else:
            rule_name = "Homerule"

        rules_dict: dict = data["rules"]

        for number, rule in rules_dict.items():
            embed.add_field(
                name=f"{rule_name} {number}",
                value=rule,
                inline=False
            )

        if data["footer"] is not None:
            embed.set_footer(text=data["footer"])

        await ctx.send(embed=embed)

    @homerules_command.command(name="set_footer", aliases=("setfooter", "setf", "changefooter", "footer"))
    async def homerules_set_footer(self, ctx: Context, footer: str):
        """
        Sets homerules footer.
        """
        data = self.get_homerules_data(ctx.guild)

        if data is None:
            await ctx.send("There is no rules! Initialize hometules before changig footer!")
            return

        if footer == "!!RESET!!":
            data["footer"] = None
        else:
            data["footer"] = footer

        self.dump_data(ctx.guild, data)

        await ctx.send("Footer changed!")

    @homerules_command.command(name="set_property", aliases=("setproperty", "property",))
    async def homerules_set_property(self, ctx: Context, property: str, *, change: str):
        """
        Sets guild's homerules properties.

        At this moment you can change: `title`, `desc`, `rulename`, `footer`.

        If you sets property to `!!RESET!!` - property will be reseted.
        """

        properties = ["title", "desc", "rulename", "footer"]

        if property not in properties:
            await ctx.send(
                "Sorry, but you can change this properties: " + ", ".join(properties)
            )
            return

        data = self.get_homerules_data(ctx.guild)

        if data is None:
            await ctx.send("There is no rules! Initialize hometules before changig properties!")
            return

        if change == "!!RESET!!":
            data[property] = None
        else:
            data[property] = change

        self.dump_data(ctx.guild, data)

        await ctx.send(f"Changed {property}!")

    @homerules_command.command(name="set_rule", aliases=("setrule", "change_rule", "changerule", "rule"))
    async def homerules_set_rule(self, ctx: Context, rule_num: int, *, change: str):
        """
        Changin homerule's description.
        """

        data = self.get_homerules_data(ctx.guild)

        if data is None:
            await ctx.send("There is no rules! Initialize hometules before changig homerules!")
            return

        data["rules"][rule_num] = change

        self.dump_data(ctx.guild, data)

        await ctx.send(f"Changed homerule {rule_num}!")

    @homerules_command.command(name="delete_rule", aliases=("del_rule", "deleterule"))
    async def homerules_del_rule(self, ctx: Context, rule_num: int):
        """
        Deletes homerule.
        """

        data = self.get_homerules_data(ctx.guild)

        if data is None:
            await ctx.send("There is no rules! Initialize hometules before changig homerules!")
            return

        try:
            del data["rules"][rule_num]
        except KeyError:
            await ctx.send(f"Rule {rule_num} doesn't exist")
            return

        self.dump_data(ctx.guild, data)

        await ctx.send(f"Deleted homerule {rule_num}!")

    @homerules_command.command(name="swap_rule", aliases=("swap", "swp"))
    async def homerules_swap_rules(self, ctx: Context, rule_a: int, rule_b: int):
        """
        Swaps homerules.
        """

        data = self.get_homerules_data(ctx.guild)

        if data is None:
            await ctx.send("There is no rules! Initialize hometules before changig homerules!")
            return

        rules: dict = data["rules"]

        if rule_a not in rules.keys():
            await ctx.send(f"There is no rules with number {rule_a}")
            return

        if rule_b not in rules.keys():
            await ctx.send(f"There is no rules with number {rule_b}")
            return

        buffer = rules[rule_a]
        rules[rule_a] = rules[rule_b]
        rules[rule_b] = buffer

        data["rules"] = rules

        self.dump_data(ctx.guild, data)

        await ctx.send(f"Swapped homerule {rule_a} and {rule_b}!")


def setup(bot: IncarnBot):
    bot.add_cog(HomeRules(bot))
