"""Reader plugin registry — maps file extensions to reader callables."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path

ReaderFn = Callable[[Path], str]

_registry: dict[str, ReaderFn] = {}

# Lazy module map: extension → dotted module path.
# Importing the module triggers its register() calls.
_LAZY_MODULES: dict[str, str] = {
    ".xlsx": "agentrag.ingestion.readers.office",
    ".pptx": "agentrag.ingestion.readers.office",
    ".csv": "agentrag.ingestion.readers.office",
    ".epub": "agentrag.ingestion.readers.ebooks",
    ".mobi": "agentrag.ingestion.readers.ebooks",
    ".json": "agentrag.ingestion.readers.structured",
    ".yaml": "agentrag.ingestion.readers.structured",
    ".yml": "agentrag.ingestion.readers.structured",
    ".xml": "agentrag.ingestion.readers.structured",
    ".toml": "agentrag.ingestion.readers.structured",
    ".srt": "agentrag.ingestion.readers.media",
    ".vtt": "agentrag.ingestion.readers.media",
    ".eml": "agentrag.ingestion.readers.email_reader",
    ".mbox": "agentrag.ingestion.readers.email_reader",
}

_loaded_modules: set[str] = set()


def register(extensions: list[str], reader: ReaderFn) -> None:
    """Register a reader function for one or more file extensions."""
    for ext in extensions:
        _registry[ext.lower()] = reader


def get_reader(extension: str) -> ReaderFn:
    """Return the reader for an extension; raise ValueError if unsupported."""
    ext = extension.lower()
    reader = _registry.get(ext)
    if reader is not None:
        return reader

    # Lazy-import the module if we know about it
    module_path = _LAZY_MODULES.get(ext)
    if module_path and module_path not in _loaded_modules:
        _loaded_modules.add(module_path)
        importlib.import_module(module_path)
        reader = _registry.get(ext)
        if reader is not None:
            return reader

    raise ValueError(f"Unsupported file type: {extension}")


def supported_extensions() -> set[str]:
    """Return all registered extensions plus all known lazy extensions."""
    return set(_registry.keys()) | set(_LAZY_MODULES.keys())
