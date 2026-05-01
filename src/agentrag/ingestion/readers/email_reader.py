"""Email readers: .eml, .mbox."""

from __future__ import annotations

import email
import mailbox
from email.message import Message
from pathlib import Path


def _extract_message_text(msg: Message) -> str:
    """Extract all plain-text parts from an email message."""
    parts: list[str] = []

    # Include key headers
    for header in ("From", "To", "Subject", "Date"):
        value = msg.get(header, "")
        if value:
            parts.append(f"{header}: {value}")

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    parts.append(payload.decode("utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if isinstance(payload, bytes):
            parts.append(payload.decode("utf-8", errors="replace"))

    return "\n".join(parts)


def read_eml(path: Path) -> str:
    """Parse an .eml file and extract headers + body text."""
    with open(path, encoding="utf-8", errors="replace") as f:
        msg = email.message_from_file(f)
    text = _extract_message_text(msg)
    if not text.strip():
        raise ValueError(f"No text content extracted from {path}.")
    return text


def read_mbox(path: Path) -> str:
    """Parse an .mbox file and extract text from all messages."""
    mbox = mailbox.mbox(str(path))
    parts: list[str] = []
    for message in mbox:
        text = _extract_message_text(message)
        if text.strip():
            parts.append(text)
    text = "\n\n---\n\n".join(parts)
    if not text.strip():
        raise ValueError(f"No text content extracted from {path}.")
    return text


# Register email readers
from agentrag.ingestion.reader_registry import register  # noqa: E402

register([".eml"], read_eml)
register([".mbox"], read_mbox)
