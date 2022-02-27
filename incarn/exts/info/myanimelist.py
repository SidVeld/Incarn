from mal import AnimeSearch, AnimeSearchResult, Anime
from textwrap import dedent

from discord import Embed
from discord.ext.commands import Cog, Context, group

from incarn.bot import IncarnBot
from incarn.pagination import LinePaginator
from incarn.log import get_logger

log = get_logger(__name__)


class MyAnimeList(Cog):
    """Commands that works with MAL api."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot

    @group(name="myanimelist", aliases=("anime", "mal"))
    async def myanimelist(self, ctx: Context) -> None:
        """
        Group of commands that works with MAL api.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @myanimelist.command(name="search")
    async def myanimelist_search(self, ctx: Context, query: str) -> None:
        """
        Searches anime titles by provided query.
        """
        log.debug(f"Trying to search with query: {query}")
        try:
            search = AnimeSearch(query)
        except ValueError:
            log.exception(f"I didn't found something with query: {query}")
            await ctx.send("I'm sorry, but I didn't find anything on your query.")
            return

        results: list[AnimeSearchResult] = search.results

        pages = []
        for result in results:
            page = f"""
            ***{result.title}***
            ────────────────────────
            {result.synopsis}

            **Score:** `{result.score}` **MAL ID:** `{result.mal_id}`
            [**Read more**]({result.url})
            """
            pages.append(page)

        embed = Embed(title="MAL Search")
        await LinePaginator.paginate(pages[:10], ctx, embed)

    @myanimelist.command(name="get")
    async def myanimelist_get(self, ctx: Context, mal_id: int) -> None:
        """
        Sends information about anime by provided mal id.
        """
        log.debug(f"Trying to get anime with mal id: {mal_id}")
        try:
            anime = Anime(mal_id)
        except ValueError:
            log.exception(f"I didn't found something with mal id: {mal_id}")
            await ctx.send("I'm sorry, but I didn't find anything with provided ID.")
            return

        anime_info = f"""
        ***[{anime.title}]({anime.url})***

        **Japanese:** `{anime.title_japanese}`
        **English:** `{anime.title_english}`

        **Type:** `{anime.type}`
        **Episodes:** `{anime.episodes}`
        **Duration:** `{anime.duration}`
        **Status:** `{anime.status}`

        **Score:** `{anime.score}` by `{anime.scored_by}` users
        **Ranked:** `{anime.rank}` **Popularity:** `{anime.popularity}`
        **Members:** `{anime.members}`

        **Synopsis:**
        {anime.synopsis}
        """

        embed = Embed(description=dedent(anime_info))
        embed.set_thumbnail(url=anime.image_url)

        await ctx.send(embed=embed)


def setup(bot: IncarnBot) -> None:
    bot.add_cog(MyAnimeList(bot))
