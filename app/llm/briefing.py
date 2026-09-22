import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.llm.prompts import BRIEFING_SYSTEM
from app.llm.provider import chat, LLMError


class Briefing(BaseModel):
    title: str
    authors: list[str]
    arxiv_id: str
    publish_date: str
    link: str
    why_this_paper_matters: str
    problem_statement: str
    method: list[str] = Field(min_length=1)
    key_results: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    follow_up_questions: list[str] = Field(min_length=1)


def _as_text(value: Any) -> str:
    """Normalize an LLM scalar/list value into a concise string."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                text = item.strip()
            else:
                text = json.dumps(item, ensure_ascii=False)
            if text:
                parts.append(text)
        return " ".join(parts)
    if value is None:
        return ""
    return str(value).strip()


def _as_string_list(value: Any) -> list[str]:
    """Normalize a string/list value into a non-empty list of strings."""
    if isinstance(value, list):
        result = []
        for item in value:
            text = _as_text(item)
            if text:
                result.append(text)
        return result
    text = _as_text(value)
    return [text] if text else []


def _extract_json_object(raw: str) -> dict:
    """Parse plain or fenced JSON without accepting arbitrary surrounding prose."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Recover the first complete JSON object when a model adds a short preamble.
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("LLM briefing response must be a JSON object.")
    return parsed


def _normalize_briefing_payload(payload: dict) -> dict:
    """Make common LLM formatting variations conform to the strict briefing schema."""
    normalized = dict(payload)
    normalized["authors"] = _as_string_list(normalized.get("authors"))
    normalized["method"] = _as_string_list(normalized.get("method"))
    normalized["key_results"] = _as_string_list(normalized.get("key_results"))
    normalized["limitations"] = _as_string_list(normalized.get("limitations"))
    normalized["follow_up_questions"] = _as_string_list(normalized.get("follow_up_questions"))
    normalized["why_this_paper_matters"] = _as_text(normalized.get("why_this_paper_matters"))
    normalized["problem_statement"] = _as_text(normalized.get("problem_statement"))

    # Some otherwise useful model responses omit one of the required list
    # fields. Preserve the strict schema while avoiding a needless hard
    # failure when the paper evidence simply does not support a richer claim.
    # These fallbacks are deliberately non-factual and do not invent paper
    # content.
    if not normalized["method"]:
        normalized["method"] = ["The supplied paper evidence does not clearly describe the method."]
    if not normalized["key_results"]:
        normalized["key_results"] = ["The supplied paper evidence does not clearly state a key result."]
    if not normalized["limitations"]:
        normalized["limitations"] = ["The supplied paper evidence does not clearly discuss limitations."]
    if not normalized["follow_up_questions"]:
        normalized["follow_up_questions"] = [
            "What additional evidence or experiments would help evaluate the paper's main claims?"
        ]
    return normalized


def _select_evidence(metadata: dict, chunks: list[dict]) -> str:
    """Select evidence across the paper rather than only the first chunks."""
    selected: list[dict] = []
    seen: set[str] = set()

    def add(chunk: dict) -> None:
        chunk_id = str(chunk.get("chunk_id", ""))
        if chunk_id not in seen:
            selected.append(chunk)
            seen.add(chunk_id)

    abstract = str(metadata.get("abstract", "")).strip()
    if abstract:
        selected.append({"page": "metadata", "section": "Abstract", "chunk_id": "metadata-abstract", "text": abstract})

    preferred = ("abstract", "introduction", "method", "approach", "experiment", "result", "discussion", "conclusion", "limitation")
    for keyword in preferred:
        matches = [c for c in chunks if keyword in str(c.get("section", "")).lower()]
        for chunk in matches[:2]:
            add(chunk)

    # Ensure the beginning and end of the document are represented as fallback evidence.
    for chunk in chunks[:2] + chunks[-2:]:
        add(chunk)

    # Bound the prompt while preserving section diversity.
    selected = selected[:20]
    return "\n\n".join(
        f"[Page {c['page']} | {c['section']} | {c['chunk_id']}]\n{c['text']}"
        for c in selected
    )


def generate_briefing(metadata: dict, parsed_text: str, chunks: list[dict]) -> dict:
    evidence = _select_evidence(metadata, chunks)
    user_prompt = f"""Paper metadata:
{json.dumps(metadata, ensure_ascii=False, indent=2)}

Paper evidence:
{evidence}

Return ONLY a JSON object with exactly these fields:
title, authors, arxiv_id, publish_date, link,
why_this_paper_matters, problem_statement,
method, key_results, limitations, follow_up_questions.

Data types are mandatory:
- title, arxiv_id, publish_date, link, why_this_paper_matters, and problem_statement: strings.
- authors, method, key_results, limitations, follow_up_questions: arrays of strings.
Do not return an array for problem_statement or why_this_paper_matters.
"""
    raw = chat(BRIEFING_SYSTEM, user_prompt)
    try:
        payload = _extract_json_object(raw)
        normalized = _normalize_briefing_payload(payload)
        result = Briefing.model_validate(normalized)
    except (json.JSONDecodeError, ValueError, ValidationError) as exc:
        raise LLMError(f"LLM briefing did not match the required JSON schema: {exc}") from exc
    return result.model_dump()
