from app.ingestion.parser import parse_pdf, PDFParseError

def test_parser_rejects_missing_file():
    try:
        parse_pdf("/does/not/exist.pdf")
    except PDFParseError:
        return
    assert False


def test_parser_extracts_abstract(tmp_path):
    import pymupdf

    pdf_path = tmp_path / "paper.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72),
        "ABSTRACT\nThis is the paper abstract.\n\n"
        "1 Introduction\nThis is the introduction.\n\n"
        "References\n[1] Example")
    # Spread filler across pages so the fixture reliably exceeds the parser's
    # minimum-text safeguard without relying on one page's printable area.
    filler = "Supporting text for the parser test. " * 80
    for i in range(0, len(filler), 900):
        p = doc.new_page()
        p.insert_textbox((72, 72, 540, 760), filler[i:i + 900])
    doc.save(pdf_path)
    doc.close()

    parsed = parse_pdf(pdf_path)
    assert "This is the paper abstract." in parsed["abstract"]
    assert parsed["has_references_section"] is True
