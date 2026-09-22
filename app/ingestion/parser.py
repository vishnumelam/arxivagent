from pathlib import Path
import pymupdf

class PDFParseError(RuntimeError):
    pass

def _section_for_text(text: str, current: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return current
    first = lines[0]
    # Conservative heading heuristic; avoids pretending that every line is a section.
    if len(first) <= 90 and (
        first.isupper()
        or first.lower() in {
            "abstract", "introduction", "background", "method", "methods",
            "experiments", "results", "discussion", "conclusion", "limitations",
            "references", "related work"
        }
        or first[:3].rstrip(".").isdigit()
    ):
        return first
    return current


def _extract_abstract(pages: list[dict]) -> str:
    """Extract a conservative abstract span from page-level PDF text."""
    full = "\n".join(p["text"] for p in pages)
    match = __import__("re").search(r"(?is)\babstract\b\s*[:\n]?\s*(.+?)(?=\n\s*(?:1\.?\s+)?introduction\b|\n\s*keywords?\b|\n\s*\d+\.?\s+[A-Z][^\n]{0,80}\n)", full)
    if match:
        return " ".join(match.group(1).split())
    return ""

def parse_pdf(path: Path) -> dict:
    try:
        doc = pymupdf.open(path)
    except Exception as exc:
        raise PDFParseError(f"Could not open PDF: {exc}") from exc

    pages = []
    total_chars = 0
    current_section = "Unknown"
    try:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            current_section = _section_for_text(text, current_section)
            pages.append({
                "page": page_number,
                "text": text,
                "section": current_section,
            })
            total_chars += len(text.strip())
    finally:
        doc.close()

    if not pages or total_chars < 1000:
        raise PDFParseError(
            "PDF extraction produced too little text to support a reliable briefing. "
            "The file may be scanned, image-based, or have an incompatible layout."
        )

    full_text = "\n\n".join(p["text"] for p in pages)
    lower = full_text.lower()
    has_references = "references" in lower or "bibliography" in lower
    abstract = _extract_abstract(pages)

    return {
        "pages": pages,
        "full_text": full_text,
        "page_count": len(pages),
        "character_count": total_chars,
        "has_references_section": has_references,
        "abstract": abstract,
    }
