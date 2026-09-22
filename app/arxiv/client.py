import re
import time
from urllib.parse import quote
import requests
import xml.etree.ElementTree as ET

from app.config import ARXIV_TIMEOUT, ARXIV_MAX_RESULTS

ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

class ArxivError(RuntimeError):
    pass

def extract_arxiv_id(value: str) -> str | None:
    value = value.strip()
    patterns = [
        r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?",
        r"^(?:arxiv:)?([0-9]{4}\.[0-9]{4,5})(?:v\d+)?$",
        r"arxiv\.org/(?:abs|pdf)/([a-z\-]+/[0-9]{7})(?:v\d+)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, value, flags=re.I)
        if match:
            return match.group(1)
    return None

def is_specific_paper(value: str) -> bool:
    return extract_arxiv_id(value) is not None

def _parse_entry(entry):
    entry_id = entry.findtext("a:id", namespaces=ATOM) or ""
    arxiv_id = extract_arxiv_id(entry_id) or ""
    title = " ".join((entry.findtext("a:title", namespaces=ATOM) or "").split())
    summary = " ".join((entry.findtext("a:summary", namespaces=ATOM) or "").split())
    published = entry.findtext("a:published", namespaces=ATOM) or ""
    updated = entry.findtext("a:updated", namespaces=ATOM) or ""
    authors = [
        (author.findtext("a:name", namespaces=ATOM) or "").strip()
        for author in entry.findall("a:author", namespaces=ATOM)
    ]
    categories = [
        c.attrib.get("term", "") for c in entry.findall("a:category", namespaces=ATOM)
    ]
    pdf_url = ""
    abs_url = ""
    for link in entry.findall("a:link", namespaces=ATOM):
        href = link.attrib.get("href", "")
        if link.attrib.get("type") == "application/pdf":
            pdf_url = href
        elif link.attrib.get("rel") == "alternate":
            abs_url = href
    if arxiv_id and not pdf_url:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "abstract": summary,
        "authors": authors,
        "published": published,
        "updated": updated,
        "categories": categories,
        "pdf_url": pdf_url,
        "abs_url": abs_url or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""),
    }

def _request(url: str, params: dict | None = None):
    headers = {"User-Agent": "AutonomousArxivPaperAgent/1.0 (educational assessment)"}
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=ARXIV_TIMEOUT)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            if attempt == 2:
                raise ArxivError(f"arXiv request failed: {exc}") from exc
            time.sleep(2 ** attempt)

def get_paper(arxiv_id: str) -> dict:
    response = _request(
        "https://export.arxiv.org/api/query",
        params={"id_list": arxiv_id},
    )
    root = ET.fromstring(response.text)
    entries = root.findall("a:entry", ATOM)
    if not entries:
        raise ArxivError(f"No arXiv paper found for ID '{arxiv_id}'.")
    return _parse_entry(entries[0])

def search_papers(topic: str, max_results: int = ARXIV_MAX_RESULTS) -> list[dict]:
    query = f'all:"{topic.strip()}"'
    response = _request(
        "https://export.arxiv.org/api/query",
        params={
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        },
    )
    root = ET.fromstring(response.text)
    return [_parse_entry(e) for e in root.findall("a:entry", ATOM)]
