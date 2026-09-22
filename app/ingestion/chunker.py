import re

def _clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def chunk_pages(pages: list[dict], chunk_size: int = 1400, overlap: int = 220) -> list[dict]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be > overlap >= 0")

    chunks = []
    chunk_index = 0

    for page in pages:
        text = _clean(page.get("text", ""))
        if not text:
            continue

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        buffer = ""

        for paragraph in paragraphs:
            candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
            if len(candidate) <= chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append({
                    "chunk_id": f"chunk_{chunk_index:04d}",
                    "page": page["page"],
                    "section": page.get("section", "Unknown"),
                    "text": buffer,
                })
                chunk_index += 1
                tail = buffer[-overlap:]
            else:
                tail = ""

            # Split unusually long paragraphs without losing overlap.
            remaining = (tail + "\n\n" + paragraph).strip() if tail else paragraph
            while len(remaining) > chunk_size:
                part = remaining[:chunk_size]
                chunks.append({
                    "chunk_id": f"chunk_{chunk_index:04d}",
                    "page": page["page"],
                    "section": page.get("section", "Unknown"),
                    "text": part.strip(),
                })
                chunk_index += 1
                remaining = remaining[chunk_size - overlap:]

            buffer = remaining

        if buffer:
            chunks.append({
                "chunk_id": f"chunk_{chunk_index:04d}",
                "page": page["page"],
                "section": page.get("section", "Unknown"),
                "text": buffer,
            })
            chunk_index += 1

    return chunks
