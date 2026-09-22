from app.ingestion.chunker import chunk_pages

def test_chunking_creates_chunks():
    pages = [{"page": 1, "section": "Introduction", "text": "word " * 1000}]
    chunks = chunk_pages(pages, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    assert all(c["page"] == 1 for c in chunks)
    assert all(c["text"] for c in chunks)

def test_invalid_chunk_settings():
    try:
        chunk_pages([{"page": 1, "text": "hello"}], 100, 100)
    except ValueError:
        return
    assert False
