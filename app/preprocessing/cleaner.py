from __future__ import annotations

import html
import re

from app.preprocessing.boilerplate import BOILERPLATE_PATTERNS


def clean_text(text: str) -> str:
    """Clean raw text for LLM consumption, preserving case."""
    if not text:
        return ""

    text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    text = html.unescape(text)
    text = text.replace("\x00", " ")
    text = re.sub(r"[\r\t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)

    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", text).strip()
