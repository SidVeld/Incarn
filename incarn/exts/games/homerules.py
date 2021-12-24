import yaml
from pathlib import Path

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Cog, Context

from incarn.bot import IncarnBot


class HomeRules(Cog):
    """Commands for managing server's homerules."""

    @commands.group(name="rules")
    async def rules_command(self, ctx: Context):
        """Commands for managing server's homerules."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @rules_command.command(name="show")
    async def rules_show(self, ctx: Context):
        """
        Sends message with homerules of this server.
        """

        rules_file = Path(f"incarn/resources/guilds/{ctx.guild.id}/rules.yml")

        try:
            rules_data: dict = yaml.load(rules_file.open(encoding="UTF-8"), Loader=yaml.FullLoader)
        except FileNotFoundError:
            await ctx.send("There is no rules.")
            return

        embed = Embed()

        if rules_data["title"] is not None:
            embed.title = rules_data["title"]
        else:
            embed.title = "Homerules"

        if rules_data["desc"] is not None:
            embed.description = rules_data["desc"]
        else:
            embed.description = "The following homerules apply:"

        if rules_data["rule_name_override"] is not None:
            rule_name = rules_data["rule_name_override"]
        else:
            rule_name = "Homerule"

        rules_dict: dict = rules_data["rules"]

        for number, rule in rules_dict.items():
            embed.add_field(
                name=f"{rule_name} {number}",
                value=rule,
                inline=False
            )

        if rules_data["footer"] is not None:
            embed.set_footer(text=rules_data["footer"])

        await ctx.send(embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(HomeRules())
