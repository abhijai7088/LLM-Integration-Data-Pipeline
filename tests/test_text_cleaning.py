from app.preprocessing.cleaner import clean_text


def test_clean_text_preserves_case() -> None:
    result = clean_text("Apple and Google are rivals.")
    assert "Apple" in result
    assert "Google" in result


def test_clean_text_removes_boilerplate() -> None:
    text = "Great article. Subscribe Now to read more."
    result = clean_text(text)
    assert "subscribe now" not in result.lower()
