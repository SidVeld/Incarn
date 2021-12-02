import cowsay

from discord import Embed
from discord.ext import commands
from discord.ext.commands.context import Context

from incarn.bot import IncarnBot


class CowSay(commands.Cog):
    """Cog for cowsay commands."""

    @commands.group(name="cowsay", aliases=("cws", "cs"))
    async def cowsay(self, ctx: commands.Context) -> None:
        """Let the cow speak!"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @cowsay.command(name="say", aliases=("s",))
    async def cowsay_say(self, ctx: Context, character: str, *, message: str) -> None:
        """
        Outputs an image of a cow (or other characters) in ASCII format with a phrase entered by the user.

        Example: cowsay say `cow` `hello world!`
        """
        if character not in list(cowsay.char_names):
            await ctx.send("Sorry, but this character con't say that!")
            return

        message = "```\n" + cowsay.get_output_string(character, message) + "\n```"
        await ctx.send(message)

    @cowsay.command(name="list", aliases=("ls", "l"))
    async def cowsay_list(self, ctx: Context) -> None:
        """
        Outputs the list of characters capable of saying your phrase.
        """
        embed = Embed(title="Cowsay")
        embed.description = "\n ".join(list(cowsay.char_names))
        await ctx.send(embed=embed, delete_after=15)


def setup(bot: IncarnBot) -> None:
    """Load the cowsay cog."""
    bot.add_cog(CowSay())
