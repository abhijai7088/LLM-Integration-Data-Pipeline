import pytest

from app.llm.parser import parse_llm_json


_VALID_JSON = """{
    "summary": "A short summary.",
    "entities": ["OpenAI", "Google"],
    "sentiment": "positive",
    "confidence_score": 0.92,
    "questions": ["Q1?", "Q2?", "Q3?"]
}"""


def test_parse_llm_json_handles_fenced_json() -> None:
    payload = parse_llm_json("```json\n" + _VALID_JSON + "\n```")
    assert payload["sentiment"] == "positive"
    assert len(payload["questions"]) == 3


def test_parse_llm_json_handles_bare_json() -> None:
    payload = parse_llm_json(_VALID_JSON)
    assert payload["confidence_score"] == pytest.approx(0.92)


def test_parse_llm_json_trailing_comma_repaired() -> None:
    bad_json = """{
        "summary": "ok",
        "entities": ["A",],
        "sentiment": "neutral",
        "confidence_score": 0.5,
        "questions": ["Q1?", "Q2?", "Q3?",]
    }"""
    payload = parse_llm_json(bad_json)
    assert payload["sentiment"] == "neutral"
