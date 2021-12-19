import os
import yaml
from pathlib import Path

from discord import Embed, Guild
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.core import guild_only

from incarn.bot import IncarnBot
from incarn.utils.helpers import load_game_reource


class Queue(commands.Cog):
    """Cog for queue's commands."""

    def __init__(self, bot: IncarnBot) -> None:
        self.bot = bot
        self.effects_dict = load_game_reource("tabletop", "effects")

        if not Path("incarn/resources/games/tabletop/queue/").exists():
            os.makedirs("incarn/resources/games/tabletop/queue/")

    @staticmethod
    def get_queue_path(guild: Guild) -> Path:
        return Path(f"incarn/resources/games/tabletop/queue/{guild.id}.yml")

    @staticmethod
    def get_queue_data(guild: Guild):
        guild_file = Queue.get_queue_path(guild)
        if not guild_file.exists():
            return FileNotFoundError
        queue_data = yaml.load(guild_file.open(encoding="utf-8"), Loader=yaml.FullLoader)
        return queue_data

    @staticmethod
    def parse_queue_data(queue_data: dict):
        queue: dict = queue_data["queue"]
        round: int = queue_data["round"]
        turn_position: int = queue_data["turn_position"]
        return queue, round, turn_position

    @staticmethod
    def get_packed_queue(queue: dict, round: int, turn_position: int) -> dict:
        return {"queue": queue, "round": round, "turn_position": turn_position}

    @staticmethod
    def set_queue_data(guild: Guild, data) -> None:
        guild_file = Path(f"incarn/resources/games/tabletop/queue/{guild.id}.yml").open(mode="w", encoding="utf-8")
        yaml.dump(data, guild_file)

    @staticmethod
    def reset_queue_data(guild: Guild) -> None:
        """
        Resets queue.
        """
        guild_file = Path(f"incarn/resources/games/tabletop/queue/{guild.id}.yml")
        if guild_file.exists():
            os.remove(guild_file)

    @staticmethod
    def sort_effect_list(effects: list[str]):
        effects.sort()
        for index, effect in enumerate(effects):
            if effect == "enemy":
                effects.pop(index)
                effects.insert(0, effect)

            if effect == "ally":
                effects.pop(index)
                effects.insert(0, effect)

            if effect == "death":
                effects.pop(index)
                effects.insert(0, effect)

        # Removes Duplicates
        effects = list(dict.fromkeys(effects))

        return effects

    def get_wrapped_queue(self, guild: Guild) -> Embed:
        """
        Wraps queue into Embed.
        """
        embed = Embed()

        queue_data = self.get_queue_data(guild)

        if queue_data is FileNotFoundError:
            return self.get_embed("Queue is not exists!", "Please create new one!")

        queue, round, turn_position = self.parse_queue_data(queue_data)

        message = ""

        for position in queue:
            character: dict = queue[position]
            effects: list[str] = character["effects"]
            line = f"{character['name']}"

            for effect in effects:

                if effect in self.effects_dict.keys():
                    line += f" {self.effects_dict[effect]['emoji']}"

            if position == turn_position:
                line = "**" + line + "**"
                turn_assigned_to = character["name"]

            message += f"{position}: {line}\n"

        embed.description = message

        embed.set_author(name="Current queue")

        embed.add_field(
            name="Current turn:",
            value=turn_assigned_to,
            inline=True
        )

        embed.add_field(
            name="Current loop:",
            value=round,
            inline=True
        )

        return embed

    def get_embed(self, title: str, message: str, color: str = 0x202225) -> Embed:
        embed = Embed(title=title, description=message, colour=color)
        return embed

    @commands.group(name="queue", aliases=("q",))
    @guild_only()
    async def queue(self, ctx: Context):
        """
        Commands for creating queue with characters. Good for battles.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @queue.command(name="create", aliases=("cr", "crt"))
    async def queue_create(self, ctx: Context, *characters: str):
        """
        Creates queue with characters.

        The queue is made up of sequentially entered character names.
        """
        if len(characters) == 0:
            return

        guild_file = Path(f"incarn/resources/games/tabletop/queue/{ctx.guild.id}.yml")
        if guild_file.exists():
            await ctx.send("Sorry, but you need to reset existing queue!")
            return

        queue = {}
        position = 1

        for character in characters:
            character = character.split("+")

            name = character[0].replace("-", " ")

            effects = character[1:]
            for index, effect in enumerate(effects):
                effects[index] = effect.lower()

            queue[position] = {"name": name, "effects": self.sort_effect_list(effects)}
            position += 1

        new_queue_data = self.get_packed_queue(queue, 1, 1)

        self.set_queue_data(ctx.guild, new_queue_data)

        await ctx.send("Queue created!")
        await self.queue_show(ctx)

    @queue.command(name="show", aliases=("s", "shw"))
    async def queue_show(self, ctx: Context):
        """
        Shows, if created, current queue.
        """
        embed = self.get_wrapped_queue(ctx.guild)
        await ctx.send(embed=embed)

    @queue.command(name="next", aliases=("n", "nxt"))
    async def queue_next(self, ctx: Context):
        """
        Transfers the right to move to the next character.
        """

        old_queue_data = self.get_queue_data(ctx.guild)

        if old_queue_data is FileNotFoundError:
            await ctx.send(embed=self.get_embed("Queue is not exists!", "Please create new one!"))
            return

        queue, round, turn_position = self.parse_queue_data(old_queue_data)

        turn_position += 1
        message = "**NEXT TURN!**"

        if turn_position > len(queue):
            turn_position = 1
            round += 1
            message += "\n ***~ NEW ROUND BEGINS ~***"

        new_queue_data = self.get_packed_queue(queue, round, turn_position)

        self.set_queue_data(ctx.guild, new_queue_data)

        await ctx.send(message)
        await self.queue_show(ctx)

    @queue.command(name="previous", aliases=("pr", "prvs"))
    async def queue_previous(self, ctx: Context):
        """
        Transfers the right to move to the previous character.
        """

        old_queue_data = self.get_queue_data(ctx.guild)

        if old_queue_data is FileNotFoundError:
            await ctx.send(embed=self.get_embed("Queue is not exists!", "Please create new one!"))
            return

        queue, round, turn_position = self.parse_queue_data(old_queue_data)

        if round < 2 and turn_position < 2:
            await ctx.send(embed=self.get_embed("Time travel error!", "I can't take a step back now."))
            return

        turn_position -= 1
        message = ("**STEP BACK!**")

        if turn_position < 1:
            turn_position = len(queue)
            round -= 1
            message += "\n***~ RETURN TO THE PREVIOUS ROUND ~***"

        new_queue_data = self.get_packed_queue(queue, round, turn_position)

        self.set_queue_data(ctx.guild, new_queue_data)

        await ctx.send(message)
        await self.queue_show(ctx)

    @queue.command(name="reset", aliases=("rs", "rst"))
    async def queue_reset(self, ctx: Context):
        """
        Resets current queue. DANGEROUS!
        """
        self.reset_queue_data(ctx.guild)
        await ctx.send("Queue reseted!")

    @queue.command(name="add")
    async def queue_add(self, ctx: Context, character: str, position: int):
        """
        Adds new character to existing Queue.
        """

        old_queue_data = self.get_queue_data(ctx.guild)

        if old_queue_data is FileNotFoundError:
            await ctx.send(embed=self.get_embed("Queue is not exists!", "Please create new one!"))
            return

        old_queue, round, current_turn = self.parse_queue_data(old_queue_data)

        character = character.split("+")

        name = character[0].replace("-", " ")

        effects = character[1:]
        for index, effect in enumerate(effects):
            effects[index] = effect.lower()

        character_dict = {"name": name, "effects": self.sort_effect_list(effects)}

        new_queue_list = list(old_queue.values())
        new_queue_list.insert(position - 1, character_dict)

        new_queue = {}
        for index, character in enumerate(new_queue_list):
            new_queue[index + 1] = character

        new_queue_data = self.get_packed_queue(new_queue, 1, 1)

        self.set_queue_data(ctx.guild, new_queue_data)

        await ctx.send(
            embed=self.get_embed(
                f"A new character appears in round {round}!",
                f"His name is {name}. Position: {position}")
            )

        await self.queue_show(ctx)

    @queue.command(name="remove", aliases=("rm", "rmv"))
    async def queue_remove(self, ctx: Context, *positions: int):
        """
        Removes Character from queue.

        You can input names or postions
        """

        old_queue_data = self.get_queue_data(ctx.guild)

        if old_queue_data is FileNotFoundError:
            await ctx.send(embed=self.get_embed("Queue is not exists!", "Please create new one!"))
            return

        old_queue, round, turn_position = self.parse_queue_data(old_queue_data)

        for position in positions:
            try:
                del old_queue[position]
                continue

            except IndexError:
                await ctx.send(embed=self.get_embed("Failed!", f"Can't find character on {position} positio!"))
                return

        new_queue = {}
        position = 1
        for character in old_queue.values():
            new_queue[position] = character
            position += 1

        while turn_position > len(new_queue):
            turn_position -= 1

        new_queue_data = self.get_packed_queue(new_queue, round, turn_position)

        self.set_queue_data(ctx.guild, new_queue_data)

        await ctx.send("Queue updated!")

    @queue.command(name="swap", aliases=("sw", "swp"))
    async def queue_swap(self, ctx: Context, pos_a: int, pos_b: int):
        """
        Swaps characters positions.
        """
        queue_data = self.get_queue_data(ctx.guild)

        if queue_data is FileNotFoundError:
            await ctx.send(embed=self.get_embed("Queue is not exists!", "Please create new one!"))
            return

        queue, round, turn = self.parse_queue_data(queue_data)

        character_a = queue[pos_a]
        character_b = queue[pos_b]

        queue[pos_a] = character_b
        queue[pos_b] = character_a

        self.set_queue_data(ctx.guild, self.get_packed_queue(queue, round, turn))

        await ctx.send("Queue updated!")
        await self.queue_show(ctx)

    @queue.command(name="inspect", aliases=("inspct", "insp"))
    async def queue_inspect(self, ctx: Context, position: int):
        """
        Shows more detailed information about the character at the specified position.

        Sends a message indicating which effects are currently acting on the character
        and when he will be able to make a move.
        """
        queue_data = self.get_queue_data(ctx.guild)

        if queue_data is FileNotFoundError:
            await ctx.send(embed=self.get_embed("Queue is not exists!", "Please create new one!"))
            return

        queue, round, current_turn = self.parse_queue_data(queue_data)

        character: dict = queue[position]

        embed = Embed()
        name: str = character["name"]
        effects: list[str] = character["effects"]

        for effect in effects:
            if effect in self.effects_dict:
                effect_data = self.effects_dict[effect]
                embed.add_field(
                    name=f"{effect_data['name']} {effect_data['emoji']}",
                    value=effect_data["desc"],
                    inline=False
                )

        queue_doubled = list(queue.keys()) * 2

        count_of_moves = 0
        for turn in queue_doubled[current_turn - 1:]:
            if position == turn:
                break
            count_of_moves += 1

        embed.add_field(
            name="Steps to move",
            value="Zero! Move now!" if count_of_moves == 0 else count_of_moves,
            inline=False
        )

        embed.title = name

        await ctx.send(embed=embed)

    @queue.command(name="addeffect", aliases=("addeff", "adde"))
    async def queue_add_effect(self, ctx: Context, position: int, *effects: str):
        """
        Adds effects to character on selected position.
        """

        queue_data = self.get_queue_data(ctx.guild)

        if queue_data is FileNotFoundError:
            await ctx.send(embed=self.get_embed("Queue is not exists!", "Please create new one!"))
            return

        queue, round, current_turn = self.parse_queue_data(queue_data)

        character = queue[position]
        character["effects"] += list(effects)

        updated_character = {"name": character["name"], "effects": self.sort_effect_list(character["effects"])}
        queue[position] = updated_character

        new_queue_data = self.get_packed_queue(queue, round, current_turn)

        self.set_queue_data(ctx.guild, new_queue_data)

        await self.queue_inspect(ctx, position)

    @queue.command(name="removeeffect", aliases=("rmveff", "rmve"))
    async def queue_remove_effect(self, ctx: Context, position: int, *effects: str):
        """
        Removes effects from character on selected position.
        """

        queue_data = self.get_queue_data(ctx.guild)

        if queue_data is FileNotFoundError:
            await ctx.send(embed=self.get_embed("Queue is not exists!", "Please create new one!"))
            return

        queue, round, current_turn = self.parse_queue_data(queue_data)

        character = queue[position]
        active_effects: list = character["effects"]

        for effect in effects:
            for index, active_effect in enumerate(active_effects):
                if active_effect == effect:
                    active_effects.pop(index)

        updated_character = {"name": character["name"], "effects": self.sort_effect_list(active_effects)}
        queue[position] = updated_character

        new_queue_data = self.get_packed_queue(queue, round, current_turn)

        self.set_queue_data(ctx.guild, new_queue_data)

        await self.queue_inspect(ctx, position)


def setup(bot: IncarnBot):
    bot.add_cog(Queue(bot))
