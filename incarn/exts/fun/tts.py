from discord.ext.commands.errors import BadArgument
import gtts
import os
from pathlib import Path

from discord import Embed
from discord.ext import commands
from discord.file import File
from discord.ext.commands.context import Context

from incarn.bot import IncarnBot
from incarn.pagination import LinePaginator


class TextToSpeach(commands.Cog):
    """TextToSpeech coomand."""

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

        await ctx.send(file=File(file_dir))

        os.remove(file_dir)


def setup(bot: IncarnBot):
    bot.add_cog(TextToSpeach())
