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
    candidate = _extract_json_object(text)
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON from LLM: {exc}") from exc

    missing = EXPECTED_KEYS - set(payload.keys())
    if missing:
        raise ValueError(f"LLM JSON missing keys: {sorted(missing)}")

    payload["entities"] = [str(x).strip() for x in payload.get("entities", []) if str(x).strip()]
    payload["questions"] = [str(x).strip() for x in payload.get("questions", []) if str(x).strip()]
    payload["summary"] = str(payload.get("summary", "")).strip()
    payload["sentiment"] = str(payload.get("sentiment", "neutral")).strip().lower()

    try:
        payload["confidence_score"] = float(payload.get("confidence_score", 0.0))
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence_score must be numeric") from exc

    if payload["sentiment"] not in {"positive", "neutral", "negative"}:
        raise ValueError("sentiment must be positive, neutral, or negative")

    return payload
