"""Structured data readers: .json, .yaml/.yml, .xml, .toml."""

from __future__ import annotations

import json
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def read_json(path: Path) -> str:
    """Pretty-print JSON as plain text for semantic indexing."""
    data: Any = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, indent=2, ensure_ascii=False)


def read_yaml(path: Path) -> str:
    """Load YAML safely and dump as text."""
    import yaml

    data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    return yaml.safe_dump(data, default_flow_style=False, allow_unicode=True)


def read_xml(path: Path) -> str:
    """Extract all text content from XML, stripping tags."""
    tree = ET.parse(str(path))
    root = tree.getroot()
    parts: list[str] = []
    for elem in root.iter():
        if elem.text and elem.text.strip():
            parts.append(elem.text.strip())
        if elem.tail and elem.tail.strip():
            parts.append(elem.tail.strip())
    return "\n".join(parts)


def read_toml(path: Path) -> str:
    """Load TOML and dump as JSON-style text for semantic indexing."""
    data: Any = tomllib.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, indent=2, ensure_ascii=False)


# Register structured data readers
from agentrag.ingestion.reader_registry import register  # noqa: E402

register([".json"], read_json)
register([".yaml", ".yml"], read_yaml)
register([".xml"], read_xml)
register([".toml"], read_toml)
