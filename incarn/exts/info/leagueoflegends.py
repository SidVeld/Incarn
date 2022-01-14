from riotwatcher import LolWatcher, ApiError

from discord import Embed
from discord.ext.commands import Cog, Context, group

from incarn.bot import IncarnBot
from incarn.constants import Keys
from incarn.log import get_logger
from incarn.pagination import LinePaginator

log = get_logger(__name__)

API_KEY = Keys.riotgames_api_key

REGIONS = {
    "br1": "br1",
    "eun1": "eune",
    "euw1": "euw1",
    "jp1": "jp1",
    "kr": "kr",
    # "la1": "la1",
    # "la2": "la2",
    "na1": "na1",
    "oc1": "oce",
    "tr1": "tr1",
    "ru": "ru"
}


class LeagueOfLegends(Cog):
    """Helpfull commands for League Of Legends players."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot
        self.watcher = LolWatcher(API_KEY)

    @group(name="league_of_legends", aliases=("lol", "LOL", "league"))
    async def league_of_legends(self, ctx: Context) -> None:
        """Helpfull assistant that can provide information about this game."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @league_of_legends.command(name="summoner", aliases=("player",))
    async def summoner(self, ctx: Context, region: str, *, name: str) -> None:
        """Sends information about summoner."""
        if region not in REGIONS:
            await ctx.send("Sorry, but you must use following region tags:\n" + ", ".join(REGIONS))
            return

        try:
            summoner: dict = self.watcher.summoner.by_name(region, name)
        except ApiError as error:
            if error.response.status_code == 404:
                await ctx.send("I can't find summoner with this name!")
                return
            elif error.response.status_code == 403:
                await ctx.send("403 - seems like our API key expired.")
                return

        embed = Embed(
            title=summoner["name"],
            description="Summoner level: " + str(summoner["summonerLevel"]),
            colour=0x2a5c55
        )

        embed.set_thumbnail(
            url=f"http://ddragon.leagueoflegends.com/cdn/10.15.1/img/profileicon/{summoner['profileIconId']}.png"
        )

        rank_data: list = self.watcher.league.by_summoner(region, summoner["id"])

        if len(rank_data) != 0:
            for data in rank_data:
                embed.add_field(name="Tier", value=data["tier"])
                embed.add_field(name="Wins", value=data["wins"])
                embed.add_field(name="Losses", value=data["losses"])
        else:
            embed.description += "\nDidnt't played ranked."

        await ctx.send(embed=embed)

    @league_of_legends.command(name="rotation", aliases=("weekly",))
    async def rotation(self, ctx: Context, region: str) -> None:
        """Sends information about current hero rotaion."""
        if region not in REGIONS.keys():
            await ctx.send("Sorry, but you must use following region tags:\n" + ", ".join(REGIONS))
            return

        rotation = self.watcher.champion.rotations(region)

        free_champions_keys = rotation["freeChampionIds"]
        free_champions_new_players_keys = rotation["freeChampionIdsForNewPlayers"]
        max_new_player_level = rotation["maxNewPlayerLevel"]

        latest_lol_version = self.watcher.data_dragon.versions_for_region(REGIONS[region])["n"]["champion"]
        champions: dict = self.watcher.data_dragon.champions(latest_lol_version, False, "en_US")["data"]

        free_champions = ""
        free_champions_new_players = ""

        for champion in champions.values():
            key = int(champion["key"])
            name = champion["name"]
            if key in free_champions_keys:
                free_champions += name + "\n"

            if key in free_champions_new_players_keys:
                free_champions_new_players += name + "\n"

        embed = Embed(
            title="Current rotation",
            description=(
                f"Latest game version: {latest_lol_version}\n"
                f"Region: {region}\n"
                f"Max new player level: {max_new_player_level}\n"
            ),
            colour=0x2a5c55
        )

        embed.add_field(
            name="Free Champions",
            value=free_champions
        )

        embed.add_field(
            name="For New Players",
            value=free_champions_new_players
        )

        await ctx.send(embed=embed)

    @league_of_legends.command(name="champion", aliases=("legend", "hero"))
    async def champion(self, ctx: Context, *, champion: str) -> None:
        """Sends information about champion."""
        try:
            latest_lol_version = self.watcher.data_dragon.versions_for_region("euw1")["n"]["champion"]
            champions: dict = self.watcher.data_dragon.champions(latest_lol_version, True, "en_US")["data"]
            # champions: dict = self.watcher.data_dragon.champions(latest_lol_version, True, "ru_RU")["data"]
        except ApiError as error:
            if error.response.status_code == 403:
                await ctx.send("403 - seems like our API key expired.")
                return

        try:
            champion_data: dict = champions[champion.replace(" ", "").capitalize()]
        except KeyError:
            await ctx.send("I can't find character with this name!")
            return

        pages = []

        champion_name: str = champion_data["name"]
        champion_title: str = champion_data["title"]
        champion_lore: str = champion_data["lore"]
        champion_image: str = champion_data["image"]["full"]
        champion_tags: list[str] = champion_data["tags"]
        champion_stats: dict = champion_data["stats"]
        champion_info: dict = champion_data["info"]

        embed = Embed()

        embed.title = f"{champion_name}, {champion_title}"
        embed.colour = 0x2a5c55
        embed.set_thumbnail(url=f"http://ddragon.leagueoflegends.com/cdn/5.9.1/img/champion/{champion_image}")
        embed.set_footer(text="; ".join(champion_tags))

        bio_page = f":pencil: **LORE**\n\n*{champion_lore}*"
        pages.append(bio_page)

        stats_page = ":bar_chart: **STATS**\n"
        stats_page += "\n".join(f"**{param.capitalize()}**: {val}" for param, val in champion_info.items())
        stats_page += "\n-------------\n"
        stats_page += "\n".join(f"**{param.capitalize()}**: {val}" for param, val in champion_stats.items())
        pages.append(stats_page)

        spell_page = ":zap: **SPELLS**"
        champion_spells: dict = champion_data["spells"]
        champion_passive: dict = champion_data["passive"]
        spell_page += f"\n\n**{champion_passive['name']} - PASSIVE**\n*{champion_passive['description']}*"
        for spell in champion_spells:
            spell_name: str = spell["name"]
            spell_desc: str = spell["description"]
            spell_desc = spell_desc.rstrip().lstrip().replace("<br>", "\n")
            spell_page += f"\n\n**{spell_name}**\n*{spell_desc}*"
        pages.append(spell_page)

        tips_page = ":books: **TIPS**"
        champion_tips = [
            ("Ally tips", champion_data["allytips"]),
            ("Enemy tips", champion_data["enemytips"])
        ]
        for category, tips in champion_tips:
            tips_page += f"\n\n**{category}**\n"
            tips_page += "\n\n".join(f"*{tip}*" for tip in tips)
        pages.append(tips_page)

        await LinePaginator.paginate(pages, ctx, embed)


def setup(bot: IncarnBot):
    if API_KEY is None:
        log.warning("The API key for riotgames is not defined. Cog disabled.")
        return
    bot.add_cog(LeagueOfLegends(bot))
