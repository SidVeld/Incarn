import discord
import random
import textwrap

from discord.ext import commands

from incarn.bot import IncarnBot


class RollColors:
    success_crit = 0x78e08f
    success = 0xb8e994
    failure = 0xe55039
    failure_crit = 0xeb2f06


class RollResults:
    CRITICAL_SUCCESS = 3
    SUCCESS = 2
    FAILURE = 1
    CRITICAL_FAILURE = 0


class WorldOfDarkness(commands.Cog):
    """Cog for World Of Darkness commands."""

    @commands.group(name="world_of_darkness", aliases=["wod"])
    async def world_of_darkness(self, ctx: commands.Context):
        """
        Commands for playing "World of Darkness".
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @world_of_darkness.command(name="roll")
    async def roll_wod(self, ctx: commands.Context, dices: int, difficult: int = 6, mod: int = 0):
        """
        Basic characteristic check for "World of Darkness".

        A dice roll is made, whose number depends on the characteristics of the character.

        Each dice is compared with the `difficult' parameter.
        If the result is greater than or equal to the parameter, one success is added to the result.
        Otherwise, nothing happens.

        If 10 drops out, the player not only gets success, but also gets an additional roll of the dice.
        If 1 drops out, the player loses one success.

        If the player has more than 0 successes by the end of the roll, the player passes the test successfully.
        If the player has exactly 0 successes, the player fails the check.
        If the player has less than 0 successes, the player fails the test with the indicator "Critical".
        """
        emb = discord.Embed(description="")

        if dices > 20 or dices <= 0:
            emb.title = "Please, stop!"
            emb.description = "Count of dices should be in range 0-20!"
            await ctx.send(embed=emb)
            return

        successes = 0
        roll_list = []

        while dices != 0:
            dice = random.randint(1, 10)
            if dice == 10:
                successes += 1
                dices += 1
            elif dice == 1:
                successes -= 1
            elif dice >= difficult:
                successes += 1
            dices -= 1
            roll_list.append(dice)

        total = successes + mod

        if total > 0:
            emb.set_author(name="SUCCESS")
            emb.color = RollColors.success
        elif total == 0:
            emb.set_author(name="FAILURE")
            emb.color = RollColors.failure
        else:
            emb.set_author(name="CRITICAL FAILURE")
            emb.color = RollColors.failure_crit

        roll_list_sorted = sorted(roll_list)

        roll_info = f"""
        Here you can learn more about your roll.

        ╔══════════════════════════════╗
        ║ {roll_list} - {len(roll_list)} rolls
        ║ {roll_list_sorted}
        ╠══════════════════════════════╣
        ║ **TARGET**: {difficult}
        ║ **SUCCESSES**: {successes}
        ║ **MOD**: {mod}
        ║ **TOTAL**: {total}
        ╚══════════════════════════════╝
        """

        emb.description = textwrap.dedent(roll_info)

        await ctx.send(embed=emb)

    @world_of_darkness.command(name="madness")
    async def roll_madness_wod(self, ctx: commands.Context, dices: int, difficult: int = 6):
        """
        A test to determine whether a vampire will fall into madness or not.

        `self-control` is used for this check.

        The character must score 5 successes in order to completely overcome the urge to violence.

        But even one success can temporarily restrain madness.
        For every Success less than 5, the character can resist insanity for one turn.
        After this time, the character can try again to gain the necessary number of successes to resist insanity.

        If the player manages to score 5 successes in a longer or shorter time,
        then the vampire manages to cope with the urges of the Beast.
        """
        embed = discord.Embed(description="")

        successes = 0
        roll_list = []

        while dices != 0:
            dice = random.randint(1, 10)
            if dice == 10:
                successes += 1
                dices += 1
            elif dice == 1:
                successes -= 1
            elif dice >= difficult:
                successes += 1
            dices -= 1
            roll_list.append(dice)

        if successes == 5:
            embed.set_author(name="Sobriety of mind has triumphed.")
            embed.description = """
                                You have managed to suppress the beast inside you.
                                """
            embed.color = RollColors.success
            embed.set_footer(text=f"{roll_list} - {successes}")
        elif successes > 0:
            embed.set_author(name="Temporary self-control.")
            embed.description = """
                                You are temporarily suppressing the beast within you. Don't relax.
                                """
            embed.color = RollColors.failure
            embed.set_footer(text=f"{roll_list} - {successes}")
        else:
            embed.set_author(name="The beast takes over.")
            embed.description = """
                                You could not overcome the beast in yourself. Prepare for the worst.
                                """
            embed.color = RollColors.failure_crit
            embed.set_footer(text=f"{roll_list} - {successes}")

        await ctx.send(embed=embed)


def setup(bot: IncarnBot):
    bot.add_cog(WorldOfDarkness())
