from app.utils.chunking import chunk_text


def test_chunk_text_returns_multiple_chunks_for_long_input() -> None:
    text = "Sentence. " * 1500
    chunks = chunk_text(text, max_chars=1000, overlap=50)
    assert len(chunks) > 1
