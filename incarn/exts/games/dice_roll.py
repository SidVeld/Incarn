
import random
import re

from discord import Embed
from discord.ext import commands
from discord.ext.commands.context import Context

from incarn.bot import IncarnBot


class DiceRoll(commands.Cog):

    @commands.command(name="roll", aliases=["r"])
    async def roll_command(self, ctx: Context, expression: str):
        """
        Classic dice roller.

        For `dice` type `{x}d{y}`.
        Where `x` - count of dices and `y` - edges of dices.

        Examples:
        `1d10` -> Rolls 1 dice with 10 edges. Returns a number from 1 to 10.
        `2d15` -> Rolls 2 dices with 15 edges. Returns two numbers from 1 to 15.
        `1d5+1` -> Rolls 1 dice with 5 edges. Returns a number from 1 to 5, to which 1 is added.
        `1d5-1` -> Rolls 1 dice with 5 edges. Returns a number from 1 to 5, from which 1 will be subtracted.
        """

        if expression.isdigit():
            expression = f"1d{expression}"

        if len(expression) < 3:
            await ctx.send("Too short!")
            return

        expression_split = expression.split("d")

        count = int(float(expression_split[0]))

        sides_and_mod = re.split("(\+|\-|\*|//|/)", expression_split[1])  # noqa W605

        sides = int(float(sides_and_mod[0]))

        mod_str = " ".join(sides_and_mod[1:])

        rolls = []

        while count > 0:
            roll = random.randint(1, sides)
            rolls.append(roll)
            count -= 1

        rolls_mod = []

        for roll in rolls:
            expr = str(roll) + mod_str
            rolls_mod.append(int(eval(expr)))

        message = "Here you go\n"

        for roll, roll_modded in zip(rolls, rolls_mod):
            roll_string = f"{roll} [ {mod_str} ] ➞ **{roll_modded}**"
            message += roll_string + "\n"

        roll_summ = 0

        for roll in rolls_mod:
            roll_summ += roll

        message += f"\n**Total**: {roll_summ}\n"

        embed = Embed()
        embed.set_author(name="Roll result")
        embed.description = message

        await ctx.send(embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(DiceRoll())
