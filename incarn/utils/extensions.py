import importlib
import inspect
import pkgutil
from typing import Iterator, NoReturn

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


EXTENSIONS = frozenset(walk_extensions())
