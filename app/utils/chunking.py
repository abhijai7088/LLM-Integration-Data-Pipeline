from __future__ import annotations

from typing import Iterable


def chunk_text(text: str, max_chars: int = 6000, overlap: int = 350) -> list[str]:
    """Chunk text into segments with overlap, attempting to break at sentences."""
    text = text.strip()
    if not text or len(text) <= max_chars:
        return [text] if text else []

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + max_chars, text_len)
        if end < text_len:
            last_break = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
            if last_break > start + max_chars // 2:
                end = last_break + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        if end >= text_len:
            break
        start = max(0, end - overlap)

    return chunks
