
import random
import re

from discord import Embed
from discord.ext import commands
from discord.ext.commands.context import Context

from incarn.bot import IncarnBot


class DiceRoll(commands.Cog):

    @commands.command(name="roll", aliases=["r"])
    async def roll_command(self, ctx: Context, dice: str, mod: int = 0):
        """
        Classic dice roller.

        For `dice` type `{x}d{y}`.
        Where `x` - count of dices and `y` - edges of dices.

        You can also use the `mod` parameter. It adds its own value to the result of the throw.
        If you get 5, and the `mod` parameter is 2, your result will change according to the formula `roll + mod`

        Examples:
        `1d10` -> Rolls 1 dice with 10 edges. Returns a number from 1 to 10.
        `2d15` -> Rolls 2 dices with 15 edges. Returns two numbers from 1 to 15.
        `1d5 1` -> Rolls 1 dice with 5 edges. Returns a number from 1 to 5, to which 1 is added.
        `1d5 -1` -> Rolls 1 dice with 5 edges. Returns a number from 1 to 5, from which 1 will be subtracted.
        """
        dice_splitted = re.split("d", dice)
        dice_count = int(dice_splitted[0])
        dice_edge = int(dice_splitted[1])

        rolls = []
        rolls_modded = []

        while dice_count > 0:
            dice_result = random.randint(1, dice_edge)
            rolls.append(dice_result)
            rolls_modded.append(dice_result + mod)
            dice_count -= 1

        result = ", ".join(str(roll) for roll in rolls)

        if mod:
            result += f"\n**Modded** ({mod})\n" + ", ".join(str(roll) for roll in rolls_modded)

        embed = Embed()
        embed.set_author(name="Roll result")
        embed.description = result

        await ctx.send(embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(DiceRoll())
