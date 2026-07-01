"""The built-in BEC catalog, shipped inside the package so `becwright add` works
offline. Each entry is a self-contained `.bec.yaml` bundle under `becs/`."""
from __future__ import annotations

from importlib import resources

_SUFFIX = ".bec.yaml"


class CatalogError(RuntimeError):
    pass


def _catalog_dir():
    return resources.files(__package__).joinpath("becs")


def catalog_names() -> list[str]:
    return sorted(
        entry.name[: -len(_SUFFIX)]
        for entry in _catalog_dir().iterdir()
        if entry.name.endswith(_SUFFIX)
    )


def read_bec(name: str) -> str:
    entry = _catalog_dir().joinpath(name + _SUFFIX)
    if not entry.is_file():
        raise CatalogError(
            f"No BEC named '{name}' in the catalog. "
            "Run `becwright search` to see what is available."
        )
    return entry.read_text(encoding="utf-8")
