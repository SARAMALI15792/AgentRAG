"""Reader plugin registry — maps file extensions to reader callables."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

ReaderFn = Callable[[Path], str]

_registry: dict[str, ReaderFn] = {}


def register(extensions: list[str], reader: ReaderFn) -> None:
    """Register a reader function for one or more file extensions."""
    for ext in extensions:
        _registry[ext.lower()] = reader


def get_reader(extension: str) -> ReaderFn:
    """Return the reader for an extension; raise ValueError if unsupported."""
    reader = _registry.get(extension.lower())
    if reader is None:
        raise ValueError(f"Unsupported file type: {extension}")
    return reader


def supported_extensions() -> set[str]:
    """Return all registered extensions."""
    return set(_registry.keys())
