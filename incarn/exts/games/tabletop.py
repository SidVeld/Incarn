import re
import random

import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands.context import Context

from incarn.bot import IncarnBot
from incarn.constants import Colours


class TableTop(commands.Cog):
    """Cog for classic tabletop commands."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot

        self.current_queue = []
        self.current_turn = 1
        self.queue_loop = 1

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

        embed = discord.Embed(colour=Colours.blue)
        embed.set_author(name="Roll result")
        embed.description = result

        await ctx.send(embed=embed)

    def reset_current_queue(self) -> None:
        """
        Resets queue.
        """
        self.current_queue = []
        self.current_turn = 1
        self.queue_loop = 1

    def wrapped_queue(self) -> Embed:
        """
        Wraps queue into Embed.
        """
        final_queue = ""

        embed = Embed()

        for character in self.current_queue:
            position = self.current_queue.index(character) + 1
            if position == self.current_turn:
                final_queue += f"{position}: **{character}**\n"
                moving_character = character
            else:
                final_queue += f"{position}: {character}\n"
            embed.description = final_queue.replace("-", " ")

        embed.set_author(name="Current queue")

        embed.add_field(
            name="Current turn:",
            value=moving_character,
            inline=True
        )

        embed.add_field(
            name="Current loop:",
            value=self.queue_loop,
            inline=True
        )

        return embed

    @commands.group(name="queue", aliases=("q",))
    async def queue(self, ctx: Context):
        """
        Commands for creating queue with characters. Good for battles.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @queue.command(name="create", aliases=("c", "cr"))
    async def queue_create(self, ctx: Context, *characters):
        """
        Creates queue with characters.

        The queue is made up of sequentially entered character names.
        """
        if len(characters) == 0:
            return

        self.reset_current_queue()

        for character in characters:
            self.current_queue.append(character.replace("-", " "))

        embed = self.wrapped_queue()

        await ctx.send("Queue created!", embed=embed)

    @queue.command(name="show", aliases=("s", "shw"))
    async def queue_show(self, ctx: Context):
        """
        Shows, if created, current queue.
        """
        if len(self.current_queue) == 0:
            return

        embed = self.wrapped_queue()

        await ctx.send(embed=embed)

    @queue.command(name="next", aliases=("n", "nxt"))
    async def queue_next(self, ctx: Context):
        """
        Transfers the right to move to the next character.
        """
        if len(self.current_queue) == 0:
            return

        self.current_turn += 1

        if self.current_turn > len(self.current_queue):
            self.current_turn = 1
            self.queue_loop += 1

        embed = self.wrapped_queue()

        await ctx.send(embed=embed)

    @queue.command(name="previous", aliases=("pr", "prvs"))
    async def queue_previous(self, ctx: Context):
        """
        Transfers the right to move to the previous character.
        """
        if len(self.current_queue) == 0:
            return

        if self.queue_loop < 2 and self.current_turn < 2:
            ctx.send("I'm sorry, I can't take a step back now. NOW.")
            return

        self.current_turn -= 1

        if self.current_turn < 1:
            self.current_turn = len(self.current_queue)
            self.queue_loop -= 1

        embed = self.wrapped_queue()

        await ctx.send(embed=embed)

    @queue.command(name="reset", aliases=("rs", "rst"))
    async def queue_reset(self, ctx: Context):
        """
        Resets current queue. DANGEROUS!
        """
        self.reset_current_queue()
        await ctx.send("Queue reseted!")

    @queue.command(name="remove", aliases=("rm", "rmv"))
    async def queue_remove(self, ctx: Context, *characters: str):
        """
        Removes Character from queue.

        You can input names or postions
        """
        if len(self.current_queue) == 0:
            return

        if len(characters) == 0:
            return

        index = 0
        for character in characters:
            if character.isdigit():
                try:
                    del self.current_queue[int(character) - 1 - index]
                    index += 1
                    continue
                except IndexError:
                    await ctx.send(f"Can't find character on {character} position.")
                    return

            if isinstance(character, str):
                try:
                    self.current_queue.remove(character)
                    continue
                except ValueError:
                    await ctx.send("Can't find this character.")
                    return

        if self.current_turn > len(self.current_queue):
            self.current_turn = 1
            self.queue_loop += 1

        embed = self.wrapped_queue()

        await ctx.send("Queue updated!", embed=embed)

    @queue.command(name="swap", aliases=("sw", "swp"))
    async def queue_swap(self, ctx: Context, pos_a: int, pos_b: int):
        """
        Swaps characters positions.
        """
        if len(self.current_queue) < 2:
            return

        buffer = self.current_queue[pos_a - 1]
        self.current_queue[pos_a - 1] = self.current_queue[pos_b - 1]
        self.current_queue[pos_b - 1] = buffer

        embed = self.wrapped_queue()

        await ctx.send("Queue updated!", embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(TableTop(bot))
