from __future__ import annotations

import json
import re
from typing import Any

EXPECTED_KEYS = {"summary", "entities", "sentiment", "confidence_score", "questions"}


def _extract_json_object(text: str) -> str:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def parse_llm_json(text: str) -> dict[str, Any]:
    """Parse and repair JSON output from the LLM."""
    candidate = _extract_json_object(text)
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON: {exc}") from exc

    missing = EXPECTED_KEYS - set(payload.keys())
    if missing:
        raise ValueError(f"Missing keys: {sorted(missing)}")

    return payload
