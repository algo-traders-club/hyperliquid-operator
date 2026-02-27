"""Strategy registry and auto-discovery."""

import importlib
import pkgutil
from pathlib import Path
from typing import List, Type

from app.strategies.base import BaseStrategy

_registry: dict[str, Type[BaseStrategy]] = {}


def register(cls: Type[BaseStrategy]) -> Type[BaseStrategy]:
    """Register a strategy class by its name."""
    _registry[cls.name] = cls  # type: ignore[attr-defined]
    return cls


def get_strategy(name: str) -> BaseStrategy:
    """Return an instance of the named strategy."""
    if name not in _registry:
        raise ValueError(f"Unknown strategy: {name}. Available: {list_strategies()}")
    return _registry[name]()


def list_strategies() -> List[str]:
    """Return list of registered strategy names."""
    return list(_registry.keys())


# Auto-discover strategy modules (excluding base and this file)
_pkg_path = Path(__file__).parent
for _importer, _modname, _ispkg in pkgutil.iter_modules([str(_pkg_path)]):
    if _modname not in ("base", "__init__"):
        importlib.import_module(f".{_modname}", __package__)
