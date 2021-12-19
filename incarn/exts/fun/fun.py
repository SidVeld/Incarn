import cowsay
import gtts
import os
import random
import yaml
from pathlib import Path
from zalgo_text import zalgo

from discord import Embed
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.errors import BadArgument
from discord.file import File

from incarn.bot import IncarnBot
from incarn.pagination import LinePaginator


class Fun(commands.Cog):
    """Commands for the entertainment of users."""

    def __init__(self, bot: IncarnBot):
        self.bot = bot

    @commands.command(name="coinflip", aliases=("flip", "coin", "cf"))
    async def coinflip_command(self, ctx: Context, side1: str = "heads", side2: str = "tails") -> None:
        """
        Flips a coin.

        You can customize sides of your coin.
        Replace `side1` and `side2` with your params.
        """
        flipped_side = random.choice([side1, side2])
        message = f"{ctx.author.name} flipperd a coin and got: **{flipped_side}**"
        await ctx.reply(message, mention_author=False)

    @commands.command(name="8ball")
    async def magic_ball(self, ctx: Context, *, question: str) -> None:
        """Return a Magic 8ball answer from answers list."""
        ANSWERS = yaml.load(Path("incarn/resources/fun/magic8ball.yml").read_text("utf8"), Loader=yaml.FullLoader)
        answer = random.choice(ANSWERS)
        await ctx.reply(answer, mention_author=False)

    @commands.command(name="casino", aliases=("csn", "slots"))
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def slots(self, ctx: Context):
        """
        Slot Machine Simulator. Slot machine simulator. Can you knock out three in a row the first time?
        """

        emojis = "🍎🍊🍐🍋🍉🍇🍓🍒"

        a = random.choice(emojis)
        b = random.choice(emojis)
        c = random.choice(emojis)

        slotmachine = f"**[ {a} {b} {c} ]**"

        if a == b == c:
            await ctx.reply(f"{slotmachine} \n Jackpot!", mention_author=False)
        elif (a == b) or (a == c) or (b == c):
            await ctx.reply(f"{slotmachine} \n 2 out of 3!", mention_author=False)
        else:
            await ctx.reply(f"{slotmachine} \n 1 out of 3, better luck next time!", mention_author=False)

    @commands.command(name="tts")
    async def tts_command(self, ctx: Context, lang_prefix: str, *text: str):
        """
        Sends an mp3 file with the voiced text.
        """

        if lang_prefix not in gtts.tts.tts_langs():
            embed = Embed()

            langs = []

            for key, value in gtts.tts.tts_langs().items():
                langs.append(f"[ {key} ] ➞ {value}")

            embed.set_author(name="List of supported languages and prefixes.")

            await LinePaginator.paginate(langs, ctx, embed, max_lines=15, empty=False)

            return

        if len(text) > 30:
            raise BadArgument("The text should not be more than 30 words.")
        if len(text) < 1:
            raise BadArgument("The text must consist of at least one word.")

        text = " ".join(text)

        temp_dir = Path("incarn/resources/tmp")

        if not temp_dir.exists():
            os.mkdir(temp_dir)

        file_dir = temp_dir / "tts.mp3"

        tts = gtts.gTTS(text, lang=lang_prefix)
        tts.save(file_dir)

        await ctx.reply(file=File(file_dir), mention_author=False)

        os.remove(file_dir)

    @commands.command(name="zalgo")
    async def zalgo_generator(self, ctx: Context, *, text: str) -> None:
        """H̱̿͢É̛̼ Ĉ̞̌O̡͎̝M̨̆͠E̵̅͘S̀̂͟"""
        text_zalgo = zalgo.zalgo().zalgofy(text)
        await ctx.reply(text_zalgo, mention_author=False)

    @commands.command()
    async def dadjoke(self, ctx: Context):
        """Gets a random dad joke."""
        url = "https://icanhazdadjoke.com/"

        async with self.bot.http_session.get(url, headers={"Accept": "text/plain"}) as response:
            result = await response.text(encoding="UTF-8")
            await ctx.reply(result, mention_author=False)

    @commands.command(name="cowsay", aliases=("cws", "cowsays"))
    async def cowsay(self, ctx: Context, character: str, *, message: str) -> None:
        """
        Outputs an image of a cow (or other characters) in ASCII format with a phrase entered by the user.

        Example: cowsay say `cow` `hello world!`
        """
        if character not in list(cowsay.char_names):
            embed = Embed(title="Cowsay")
            embed.description = "\n ".join(list(cowsay.char_names))
            await ctx.reply(
                "Sorry, but this character can't say that! Here the list:",
                embed=embed,
                mention_author=False
            )
            return

        message = "```\n" + cowsay.get_output_string(character, message) + "\n```"
        await ctx.reply(message, mention_author=False)


def setup(bot: IncarnBot) -> None:
    """Load the Fun cog."""
    bot.add_cog(Fun(bot))
