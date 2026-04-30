"""Tests for the reader plugin registry."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_register_and_lookup() -> None:
    """Registered reader is returned by get_reader for its extension."""
    from agentrag.ingestion import reader_registry

    reader_registry._registry.clear()

    def _fake_reader(path: Path) -> str:
        return "fake"

    reader_registry.register([".fake"], _fake_reader)
    assert reader_registry.get_reader(".fake") is _fake_reader


def test_register_multiple_extensions() -> None:
    """One reader can be registered for multiple extensions."""
    from agentrag.ingestion import reader_registry

    reader_registry._registry.clear()

    def _multi(path: Path) -> str:
        return "multi"

    reader_registry.register([".a", ".b", ".c"], _multi)
    assert reader_registry.get_reader(".a") is _multi
    assert reader_registry.get_reader(".b") is _multi
    assert reader_registry.get_reader(".c") is _multi


def test_get_reader_unknown_extension_raises() -> None:
    """get_reader raises ValueError with actionable message for unknown extension."""
    from agentrag.ingestion import reader_registry

    reader_registry._registry.clear()

    with pytest.raises(ValueError, match="Unsupported file type: .xyz"):
        reader_registry.get_reader(".xyz")


def test_supported_extensions_returns_set() -> None:
    """supported_extensions returns all registered extensions as a set."""
    from agentrag.ingestion import reader_registry

    reader_registry._registry.clear()

    def _r(path: Path) -> str:
        return ""

    reader_registry.register([".p", ".q"], _r)
    exts = reader_registry.supported_extensions()
    assert isinstance(exts, set)
    assert ".p" in exts
    assert ".q" in exts


def test_extension_normalized_to_lowercase() -> None:
    """Extensions are stored and looked up case-insensitively."""
    from agentrag.ingestion import reader_registry

    reader_registry._registry.clear()

    def _r(path: Path) -> str:
        return ""

    reader_registry.register([".TXT"], _r)
    assert reader_registry.get_reader(".txt") is _r
    assert reader_registry.get_reader(".TXT") is _r


def test_later_registration_overwrites() -> None:
    """Re-registering an extension replaces the previous reader."""
    from agentrag.ingestion import reader_registry

    reader_registry._registry.clear()

    def _first(path: Path) -> str:
        return "first"

    def _second(path: Path) -> str:
        return "second"

    reader_registry.register([".dup"], _first)
    reader_registry.register([".dup"], _second)
    assert reader_registry.get_reader(".dup") is _second
