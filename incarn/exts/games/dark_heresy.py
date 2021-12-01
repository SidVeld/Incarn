import random
import textwrap

from typing import Optional

import discord
from discord.ext import commands

from incarn.bot import IncarnBot
from incarn.utils.helpers import load_game_reource


class DH_Colours:
    success_crit = 0x78e08f
    success = 0xb8e994
    failure = 0xe55039
    failure_crit = 0xeb2f06

    green = 0x2ecc71
    red = 0xe74c3c
    orange = 0xe67e22
    dark_orange = 0xd35400
    yellow = 0xf1c40f
    purple = 0xD980FA
    dark_red = 0xc0392b
    dark_green = 0x27ae60


class DarkHeresy(commands.Cog):
    """Cog for Dark Heresy commands."""

    @commands.group(name="dark_heresy", aliases=["dh"])
    async def dark_heresy(self, ctx: commands.Context):
        """
        Commands for playing "Dark Heresy".
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @dark_heresy.command(name="book", aliases=["books"])
    async def book_dark_heresy(self, ctx: commands.Context):
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
    async def roll_dark_heresy(self, ctx: commands.Context, char_lvl: int, mod: Optional[int] = 0):
        """
        Basic characteristic check for "Dark Heresy".

        Makes a throw of one dice D100.
        Its result is compared with `char_lvl` taking into account `mod`.
        If the result of the throw is less than `char_lvl`, the player passes the test. Otherwise, it fails.

        Don't forget that Psykers have a unique "doubles" mechanic.
        """
        emb = discord.Embed()

        dice = random.randint(1, 100)
        total = dice + mod

        if total == 1:
            result = "CRITICAL SUCCESS"
        elif total == 100:
            result = "CRITICAL FAILURE"
        elif total <= char_lvl:
            result = "SUCCESS"
        else:
            result = "FAILURE"

        # =====
        # Disabled untill 3.10
        # =====
        # match result:
        #     case "CRITICAL SUCCESS":
        #         emb.color = DH_Colours.yellow

        #     case "SUCCESS":
        #         emb.color = DH_Colours.green

        #     case "FAILURE":
        #         emb.color = DH_Colours.orange

        #     case "CRITICAL FAILURE":
        #         emb.color = DH_Colours.red

        if result == "CRITICAL SUCCESS":
            emb.color = DH_Colours.yellow
        elif result == "SUCESS":
            emb.color = DH_Colours.green
        elif result == "FAILURE":
            emb.color = DH_Colours.orange
        elif result == "CRITICAL FAILURE":
            emb.color = DH_Colours.red

        emb.set_author(name=result)

        difference = char_lvl - total
        if difference < 0:
            difference *= -1
        degrees = difference // 10

        roll_info = f"""
        Here you can learn more about your roll.
        ────────────────────────
        **You**: {dice} + {mod} = {total}
        **Target**: {char_lvl}
        **Degrees**: {degrees}
        """

        a, b = divmod(total, 10)
        if a == b:
            emb.add_field(
                name="PSYCHIC PHENOMENA",
                value=f"We got **{total}**! If you are psyker - use subcommand `phenomenon`!"
            )
            emb.color = DH_Colours.purple

        emb.description = textwrap.dedent(roll_info)

        await ctx.send(embed=emb)

    @dark_heresy.command(name="phenomenon", aliases=["ph", "rph", "phenomena"])
    async def roll_psy_phenomenon(self, ctx: commands.Context):
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
    async def roll_hitlocation(self, ctx: commands.Context, count: int = 1):
        """creates embed"""

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
