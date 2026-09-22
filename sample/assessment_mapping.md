# Assessment Requirement Mapping

This document is for internal review before submission.

## Required core pipeline

1. Query understanding — `app/graph/nodes.py::understand_query`
2. arXiv retrieval — `search_arxiv_node`
3. Selection/ranking — `select_paper_node`
4. Fetch & parse — `fetch_pdf_node`, `parse_pdf_node`
5. Chunk & embed — `chunk_and_index_node`
6. Summarize — `briefing_node`
7. QA loop — `app/llm/qa.py` + CLI

## Required executive briefing fields

Implemented by `app/llm/briefing.py::Briefing`:

- Title
- Authors
- arXiv ID
- Publish date
- Link
- Why this paper matters
- Problem statement
- Method / approach
- Key results / claims
- Limitations
- Suggested follow-up questions

## Grounding

QA retrieves top-k chunks from the local FAISS index. Each result retains page, section, chunk ID, and similarity. A minimum similarity threshold can reject weak evidence before LLM generation.

## Realistic failures

- Empty arXiv result
- arXiv/network failure
- Invalid arXiv input
- PDF download failure
- non-PDF response
- corrupt/unreadable PDF
- low extracted text density
- insufficient chunks
- vector indexing failure
- LLM/provider failure
- low-similarity QA question

## Out of scope

- Frontend beyond CLI
- Multi-user auth
- Deployment/production infrastructure
- Non-arXiv sources
- Fine-tuning


## Robustness additions in v3
- Normalizes common LLM JSON type drift before Pydantic validation (for example, a list returned for `problem_statement`).
- Accepts fenced JSON while still requiring a JSON object and strict schema validation.
- Selects briefing evidence across abstract, introduction, methods, results, discussion/conclusion, and document boundaries instead of only the first chunks.
- Persists a conservatively extracted PDF abstract alongside page/section text.
- Adds regression tests for malformed briefing output and evidence selection.
