import importlib
import inspect
import pkgutil
from collections.abc import Iterator
from typing import NoReturn

from discord.ext.commands import Context

from incarn import exts


def unqualify(name: str) -> str:
    """Returns an unqualified name given a qualified module/package `name`."""
    return name.rsplit(".", maxsplit=1)[-1]


def walk_extensions() -> Iterator[str]:
    """Yield extension names from the incarn.exts subpackage."""

    def on_error(name: str) -> NoReturn:
        raise ImportError(name=name)

    for module in pkgutil.walk_packages(exts.__path__, f"{exts.__name__}.", onerror=on_error):
        if unqualify(module.name).startswith("_"):
            continue

        if module.ispkg:
            imported = importlib.import_module(module.name)
            if not inspect.isfunction(getattr(imported, "setup", None)):
                continue

        yield module.name


async def invoke_help_command(ctx: Context) -> None:
    """Invoke the help command or default help command if help extensions is not loaded."""
    if "bot.exts.core.help" in ctx.bot.extensions:
        help_command = ctx.bot.get_command("help")
        await ctx.invoke(help_command, ctx.command.qualified_name)
        return
    await ctx.send_help(ctx.command)

EXTENSIONS = frozenset(walk_extensions())
