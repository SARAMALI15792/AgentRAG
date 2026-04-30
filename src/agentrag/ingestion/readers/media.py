"""Subtitle readers: .srt, .vtt."""

from __future__ import annotations

from pathlib import Path


def read_srt(path: Path) -> str:
    """Extract timestamped text segments from an SRT subtitle file."""
    try:
        import pysrt
    except ImportError:
        raise ImportError(
            "pysrt is required for .srt support. "
            "Install it with: pip install agentrag[web]"
        ) from None

    subs = pysrt.open(str(path), encoding="utf-8")
    parts: list[str] = []
    for sub in subs:
        timestamp = f"[{sub.start} --> {sub.end}]"
        parts.append(f"{timestamp} {sub.text}")
    return "\n".join(parts)


def read_vtt(path: Path) -> str:
    """Extract cue text from a WebVTT subtitle file."""
    try:
        import webvtt
    except ImportError:
        raise ImportError(
            "webvtt-py is required for .vtt support. "
            "Install it with: pip install agentrag[web]"
        ) from None

    parts: list[str] = []
    for caption in webvtt.read(str(path)):
        parts.append(f"[{caption.start} --> {caption.end}] {caption.text}")
    return "\n".join(parts)


# Register subtitle readers
from agentrag.ingestion.reader_registry import register  # noqa: E402

register([".srt"], read_srt)
register([".vtt"], read_vtt)
