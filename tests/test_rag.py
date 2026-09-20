from app.rag import chunk_text


def test_chunk_text_splits_with_overlap():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=800, overlap=100)

    assert len(chunks) == 2
    assert chunks[0] == "a" * 800
    # second chunk starts 100 chars before the end of the first (the overlap)
    assert chunks[1] == "a" * 300


def test_chunk_text_single_chunk_for_short_text():
    chunks = chunk_text("short text", chunk_size=800, overlap=100)

    assert chunks == ["short text"]
