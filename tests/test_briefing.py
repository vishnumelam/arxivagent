import json

from app.llm import briefing as briefing_module


def test_normalize_briefing_payload_converts_problem_statement_list():
    payload = {
        "authors": ["A", "B"],
        "problem_statement": ["First point.", "Second point."],
        "why_this_paper_matters": ["Important.", "Useful."],
        "method": "Uses attention.",
        "key_results": ["Result 1"],
        "limitations": "Limited evaluation.",
        "follow_up_questions": ["Question?"],
    }
    normalized = briefing_module._normalize_briefing_payload(payload)
    assert normalized["problem_statement"] == "First point. Second point."
    assert normalized["why_this_paper_matters"] == "Important. Useful."
    assert normalized["method"] == ["Uses attention."]
    assert normalized["limitations"] == ["Limited evaluation."]


def test_extract_json_object_handles_markdown_fence():
    raw = '```json\n{"problem_statement":"A"}\n```'
    assert briefing_module._extract_json_object(raw) == {"problem_statement": "A"}


def test_extract_json_object_rejects_non_object():
    try:
        briefing_module._extract_json_object(json.dumps(["not", "an", "object"]))
    except ValueError:
        return
    assert False


def test_select_evidence_includes_abstract_and_multiple_sections():
    metadata = {"abstract": "Paper abstract evidence."}
    chunks = [
        {"page": 1, "section": "Introduction", "chunk_id": "i1", "text": "intro"},
        {"page": 2, "section": "Methods", "chunk_id": "m1", "text": "method"},
        {"page": 3, "section": "Results", "chunk_id": "r1", "text": "results"},
        {"page": 4, "section": "Conclusion", "chunk_id": "c1", "text": "conclusion"},
    ]
    evidence = briefing_module._select_evidence(metadata, chunks)
    assert "Paper abstract evidence." in evidence
    assert "method" in evidence
    assert "results" in evidence
    assert "conclusion" in evidence


def test_normalize_briefing_payload_fills_empty_required_lists():
    payload = {
        "authors": ["A"],
        "method": [],
        "key_results": [],
        "limitations": [],
        "follow_up_questions": [],
    }
    normalized = briefing_module._normalize_briefing_payload(payload)
    assert normalized["method"]
    assert normalized["key_results"]
    assert normalized["limitations"]
    assert normalized["follow_up_questions"]
    assert "does not clearly" in normalized["limitations"][0]
