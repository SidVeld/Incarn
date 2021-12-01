import discord
import random
import textwrap

from discord.ext import commands

from incarn.bot import IncarnBot
from incarn.constants import Colours
from incarn.utils.helpers import load_game_reource


class DiscoColors:
    disco_blue = 0x5bc3d7
    disco_green = 0x9cc222
    disco_orange = 0xf8961e
    disco_purple = 0x7454ce
    disco_red = 0xcb466a
    disco_yellow = 0xe3b834


class DiscoElysium(commands.Cog):
    """Cog for Disco Elysium commands."""

    @commands.group(name="disco_elysium", aliases=["de", "disco"])
    async def disco_elysium(self, ctx: commands.Context):
        """
        Commands based on the game "Disco Elysium".

        What kind of cop are you?

        Don't forget to turn on PROTORAVE !!!
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @disco_elysium.command(name="roll")
    async def roll_disco(self, ctx: commands.Context, skill_level: int, difficult: int, mod: int = 0):
        """
        Makes a roll of two dice. Their sum is added with the parameter `skill_level` and `mod` . \
        If the total amount is greater than or equal to the `difficult` parameter, \
        the roll is considered successful.

        `skill_level` and `difficult` should be between 1 and 20.

        Please note that if you get two ones, you will automatically fail the roll marked "critical failure". \
        The same goes for the two sixes, but in the opposite direction.
        """
        emb = discord.Embed()

        if skill_level <= 0 or skill_level > 20:
            emb.title = "Sir, stop!"
            emb.description = "The parameter `skill_level` must be between 1 and 20!"
            emb.color = Colours.soft_orange
            await ctx.send(embed=emb)
            return

        if difficult <= 0 or difficult > 20:
            emb.title = "Sir, stop!"
            emb.description = "The parameter `difficult` must be between 1 and 20!"
            emb.color = Colours.soft_orange
            await ctx.send(embed=emb)
            return

        dice_1 = random.randint(1, 6)
        dice_2 = random.randint(1, 6)
        dice_summ = dice_1 + dice_2
        total = skill_level + dice_summ + mod

        if dice_1 == dice_2 == 6:
            result = "CRITICAL SUCCESS"
        elif dice_1 == dice_2 == 1:
            result = "CRITICAL FAILURE"
        elif total >= difficult:
            result = "SUCCESS"
        else:
            result = "FAILURE"

        if result == "CRITICAL SUCCESS":
            emb.color = DiscoColors.disco_green
        elif result == "SUCCESS":
            emb.color = DiscoColors.disco_green
        elif result == "FAILURE":
            emb.color = DiscoColors.disco_orange
        elif result == "CRITICAL FAILURE":
            emb.color = DiscoColors.disco_orange

        # match result:
        #     case "CRITICAL SUCCESS":
        #         emb.color = DiscoColors.disco_green
        #     case "SUCCESS":
        #         emb.color = DiscoColors.disco_green
        #     case "FAILURE":
        #         emb.color = DiscoColors.disco_orange
        #     case "CRITICAL FAILURE":
        #         emb.color = DiscoColors.disco_orange

        # match difficult:
        #     case 20:
        #         difficult_text = "Impossible"
        #     case 19:
        #         difficult_text = "Impossible"
        #     case 18:
        #         difficult_text = "Impossible"
        #     case 17:
        #         difficult_text = "Godly"
        #     case 16:
        #         difficult_text = "Godly"
        #     case 15:
        #         difficult_text = "Heroic"
        #     case 14:
        #         difficult_text = "Legendary"
        #     case 13:
        #         difficult_text = "Formidable"
        #     case 12:
        #         difficult_text = "Challenging"
        #     case 11:
        #         difficult_text = "Medium"
        #     case 10:
        #         difficult_text = "Medium"
        #     case 9:
        #         difficult_text = "Easy"
        #     case 8:
        #         difficult_text = "Easy"
        #     case _:
        #         difficult_text = "Trival"

        roll_info = f"""
        Here you can learn more about your roll.

        **Difficult**: ({difficult})
        VS
        **Total (you have)**: {total}
        ────────────────────────
        • **Skill**: {skill_level}
        • **Dices**: {dice_1} + {dice_2} = {dice_1 + dice_2}
        • **Mod**: {mod}
        """

        emb.description = textwrap.dedent(roll_info)

        emb.set_author(name=result)
        emb.set_footer(text="1:1 - Crit Failure. 6:6 - Crit Success.")

        await ctx.send(embed=emb)

    @disco_elysium.command(name="whisper")
    async def whisper_disco(self, ctx: commands.Context, skill: str, *, text: str):
        """
        Sends embed message as skill from Disco Elysium.

        Spaces and dashes should be replaced with underscore (`_`)
        """
        embed = discord.Embed()

        skill_list = load_game_reource("disco_elysium", "skills")

        try:
            skill_data = skill_list[skill.lower()]
        except KeyError:
            embed.set_author(name="Skill not found.")
            embed.description = "I can't find that skill. Try again."
            embed.color = Colours.red
            await ctx.send(embed=embed, delete_after=5)
            return

        skill_name = skill_data["name"]
        skill_color = skill_data["color"]
        skill_portrair = skill_data["portrait"]

        embed.description = text
        embed.colour = skill_color
        embed.set_author(name=skill_name)
        embed.set_thumbnail(url=skill_portrair)

        await ctx.send(embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(DiscoElysium(bot))
