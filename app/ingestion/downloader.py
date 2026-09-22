from pathlib import Path
import requests

def download_pdf(pdf_url: str, destination: Path, timeout: int = 60) -> Path:
    headers = {"User-Agent": "AutonomousArxivPaperAgent/1.0 (educational assessment)"}
    try:
        with requests.get(pdf_url, headers=headers, timeout=timeout, stream=True) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not pdf_url.lower().endswith(".pdf"):
                # arXiv may omit/alter the content-type; inspect magic bytes below.
                pass
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        handle.write(chunk)
    except requests.RequestException as exc:
        raise RuntimeError(f"PDF download failed: {exc}") from exc

    with destination.open("rb") as handle:
        magic = handle.read(5)
    if magic != b"%PDF-":
        destination.unlink(missing_ok=True)
        raise RuntimeError("Downloaded content is not a valid PDF.")
    return destination
