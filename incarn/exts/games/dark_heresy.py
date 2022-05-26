import random
import textwrap

from typing import Optional

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context

from incarn.bot import IncarnBot
from incarn.utils.helpers import load_game_reource
from incarn.constants import Bot


class DH_Colours:
    success_crit = 0x72d653
    success = 0x5d9957
    failure = 0x8b292a
    failure_crit = 0xeb2f06

    green = 0x5fb145
    red = 0xe74c3c
    orange = 0xe67e22
    dark_orange = 0xd35400
    yellow = 0xf1c40f
    purple = 0xD980FA
    dark_red = 0xc0392b
    dark_green = 0x27ae60


class Results:
    success = "Success"
    failure = "Failure"
    critical_success = "Critical Success!"
    critical_failure = "Critical Failure!"


class DarkHeresy(Cog):
    """
    Commands for the board role-playing game "Dark Heresy".
    Will you become the best acolyte in the system?
    """

    @commands.group(name="dark_heresy", aliases=["dh"])
    async def dark_heresy(self, ctx: Context):
        """
        Commands for the board role-playing game "Dark Heresy".
        Will you become the best acolyte in the system?
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @dark_heresy.command(name="book", aliases=["books"])
    async def book_dark_heresy(self, ctx: Context):
        """
        Sends links to rulebooks known to the bot.
        """
        embed = discord.Embed(color=DH_Colours.dark_red)
        embed.set_author(name="Books for Dark Heresy")
        books = load_game_reource("dark_heresy", "books")

        for book in books.values():
            name = book["name"]
            url = book["url"]
            source = book["source"]
            format = book["format"]
            embed.add_field(
                name=name,
                value=f"[Link - {source} ({format})]({url})",
                inline=False
            )

        await ctx.send(embed=embed)

    @dark_heresy.command(name="roll")
    async def roll_dark_heresy(self, ctx: Context, skill: int, modifer: Optional[int] = 0):
        """
        Basic characteristic check for "Dark Heresy".

        Makes a throw of one dice D100.
        Its result is compared with `char_lvl` taking into account `mod`.
        If the result of the throw is less than `char_lvl`, the player passes the test. Otherwise, it fails.

        Don't forget that Psykers have a unique "doubles" mechanic.
        """
        emb = discord.Embed()

        roll = random.randint(1, 100)
        target = skill + modifer

        if roll == 1:
            result = Results.critical_success
        elif roll == 100:
            result = Results.critical_failure
        elif roll <= target:
            result = Results.success
        else:
            result = Results.failure

        match result:
            case Results.critical_success:
                emb.color = DH_Colours.success_crit
            case Results.success:
                emb.color = DH_Colours.success
            case Results.failure:
                emb.color = DH_Colours.failure
            case Results.critical_failure:
                emb.color = DH_Colours.failure_crit

        emb.set_author(name=result)

        degrees = (target // 10) - (roll // 10)

        roll_info = f"""
        Here you can learn more about your roll.
        ─ • ──────────────────────
        **Skill**: `{skill}`
        **Modifer**: `{modifer}`
        **Target**: `{target}`
        ────────────────────────
        **Roll**: `{roll}`
        **Degrees**: `{degrees}`
        """

        emb.description = textwrap.dedent(roll_info)

        await ctx.send(embed=emb)

        first_number, second_number = divmod(roll, 10)
        if first_number == second_number:
            roll_info = f"""
            ***PSYCHIC PHENOMENA***
            ────────────────────────
            We got **{roll}**!
            If you are psyker - use subcommand:
            `{Bot.prefix}dark_heresy phenomenon`
            """
            emb.set_author(name="Warning!")
            emb.description = textwrap.dedent(roll_info)
            emb.color = DH_Colours.purple

            await ctx.send(embed=emb)

    @dark_heresy.command(name="phenomenon", aliases=["ph", "rph", "phenomena"])
    async def roll_psy_phenomenon(self, ctx: Context):
        """
        Rolls random PSY-phenomenon.

        If Psyker and you sudenly rolled something like `55` or `11` or `44` - you should use this command.
        """
        embed = discord.Embed(color=DH_Colours.purple)
        result = random.randint(1, 100)

        # It looks weird but better than ELIF/ELIF/ELIF
        index = 0
        if 1 <= result <= 3:
            index = 1
        elif 4 <= result <= 5:
            index = 2
        else:
            for i in range(2, 25):
                if 3 * i <= result <= 3 * i + 2:
                    index = i + 1
                    break

        # If rolled out of range 1-74 - we got 26th index.
        if not index:
            index = 26

        ph_list = load_game_reource("dark_heresy", "psy_phenomena")
        ph_name: str = ph_list[f"event_{index}"]["name"]
        ph_desc: str = ph_list[f"event_{index}"]["desc"]

        embed.set_author(name=ph_name.upper())
        embed.description = ph_desc
        embed.set_footer(text=f"Roll result: {result}")

        await ctx.send(embed=embed)

    @dark_heresy.command(name="hitlocation", aliases=("hl",))
    async def roll_hitlocation(self, ctx: Context, count: int = 1):
        """
        Determines which part of the body the attack will hit.

        The `count` parameter can be replaced with another integer.
        This parametr determines the number of attacks to be checked.
        """

        if count <= 0:
            count = 1
        elif count > 8:
            count = 8

        embed = discord.Embed(color=DH_Colours.dark_red)
        embed.set_author(name="Hit Location")

        location_list = []

        for loop in range(1, count + 1):
            roll = random.randint(1, 100)

            if 1 <= roll <= 10:
                bodypart = "HEAD"
            elif 11 <= roll <= 20:
                bodypart = "RIGHT ARM"
            elif 21 <= roll <= 30:
                bodypart = "LEFT ARM"
            elif 31 <= roll <= 70:
                bodypart = "BODY"
            elif 71 <= roll <= 85:
                bodypart = "RIGHT LEG"
            else:
                bodypart = "LEFT LEG"

            location_list.append(f"{loop}: {bodypart} ({roll})")

        result = """
        These body parts are selected.
        ──────────────────────────────
        """
        result = textwrap.dedent(result)
        result += "\n".join(location for location in location_list)

        embed.description = result

        await ctx.send(embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(DarkHeresy())
