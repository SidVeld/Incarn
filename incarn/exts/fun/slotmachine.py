import random

from discord.ext import commands

from incarn.bot import IncarnBot


class SlotMachine(commands.Cog):
    """Cog for SlotMachine command"""

    @commands.command(aliases=["casino"])
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def slots(self, ctx: commands.Context):
        """
        Slot Machine Simulator. Slot machine simulator. Can you knock out three in a row the first time?
        """

        emojis = "🍎🍊🍐🍋🍉🍇🍓🍒"

        a = random.choice(emojis)
        b = random.choice(emojis)
        c = random.choice(emojis)

        slotmachine = f"**[ {a} {b} {c} ]**"

        if a == b == c:
            await ctx.send(f"{slotmachine} \n Jackpot!")
        elif (a == b) or (a == c) or (b == c):
            await ctx.send(f"{slotmachine} \n 2 out of 3!")
        else:
            await ctx.send(f"{slotmachine} \n 1 out of 3, better luck next time!")


def setup(bot: IncarnBot):
    bot.add_cog(SlotMachine())
