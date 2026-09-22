# Autonomous arXiv Paper Digest & QA Agent

A small, stateful research agent built for the AI Intern assessment.

The agent accepts:

* A natural-language research topic
* A specific arXiv ID
* An arXiv URL

It retrieves an arXiv paper, parses the PDF, chunks and embeds the paper into a local FAISS index, generates a structured executive briefing, and provides follow-up question answering using retrieval-augmented generation (RAG).

The project focuses on stateful agent design, retrieval quality, grounded answers, failure handling, and explainable engineering choices rather than UI polish.

---

## 1. What This Project Does

The application implements the following flow:

```text
User Input
    |
    v
Query Understanding
    |
    +------------------------------+
    |                              |
    | Topic                        | Specific arXiv ID / URL
    v                              v
arXiv Search                  Direct Paper Lookup
    |                              |
    v                              |
Candidate Ranking                  |
    |                              |
    +---------------+--------------+
                    |
                    v
                Fetch PDF
                    |
                    v
              Parse with PyMuPDF
                    |
                    v
              Chunk the Paper
                    |
                    v
          Sentence Transformer
               Embeddings
                    |
                    v
                FAISS Index
                    |
                    v
            Executive Briefing
                    |
                    v
                 QA Mode
                    |
                    v
            Retrieve Top-K Chunks
                    |
                    v
             Grounded LLM Answer
```

---

## 2. Assessment Requirements Covered

| Assessment Requirement                    | Implementation                                                        |
| ----------------------------------------- | --------------------------------------------------------------------- |
| Topic or arXiv ID/URL input               | `app/arxiv/client.py`, `app/graph/nodes.py`                           |
| Explicit stateful graph                   | LangGraph `StateGraph` in `app/graph/workflow.py`                     |
| Query understanding                       | `understand_query` node                                               |
| Official arXiv retrieval                  | arXiv Atom API                                                        |
| Topic candidate retrieval                 | arXiv search API                                                      |
| Candidate selection/ranking               | `app/arxiv/ranking.py`                                                |
| PDF fetching                              | `app/ingestion/downloader.py`                                         |
| PDF parsing                               | PyMuPDF                                                               |
| Abstract extraction                       | `app/ingestion/parser.py`                                             |
| Section/reference detection               | PDF parser                                                            |
| Chunking                                  | `app/ingestion/chunker.py`                                            |
| Embeddings                                | Sentence Transformers                                                 |
| Local vector database                     | FAISS                                                                 |
| Structured executive briefing             | Pydantic schema + LLM                                                 |
| Grounded QA                               | Top-K FAISS retrieval + context-only prompt                           |
| Unsupported-question refusal              | Similarity threshold + grounded prompt                                |
| State persistence                         | Graph state + persisted FAISS/metadata/session JSON                   |
| Failure handling                          | Query, search, download, parsing, indexing, briefing, and QA failures |
| Automated tests                           | pytest                                                                |
| User interface                            | CLI                                                                   |
| Paid API not required                     | Groq is optional; Ollama local fallback is supported                  |
| Non-arXiv sources                         | Intentionally unsupported                                             |
| Full frontend/deployment/auth/fine-tuning | Intentionally out of scope                                            |

---

## 3. Architecture

### 3.1 LangGraph Workflow

The project uses an explicit LangGraph state graph rather than a single monolithic prompt.

```text
                         START
                           |
                           v
                  +-------------------+
                  | understand_query  |
                  +---------+---------+
                            |
                   +--------+--------+
                   |                 |
                 topic             direct
                   |                 |
                   v                 v
           +---------------+  +------------------+
           | search_arxiv  |  | get_direct_paper |
           +-------+-------+  +--------+---------+
                   |                    |
                   v                    |
           +---------------+            |
           | select_paper  |------------+
           +-------+-------+
                   |
                   v
             +-------------+
             |  fetch_pdf  |
             +------+------+
                    |
                    v
             +-------------+
             |  parse_pdf  |
             +------+------+
                    |
                    v
           +------------------+
           | chunk_and_index  |
           +---------+--------+
                     |
                     v
           +------------------+
           | generate_briefing|
           +---------+--------+
                     |
                     v
             +-------------+
             | save_session|
             +------+------+
                    |
                    v
                   END
```

After the graph completes, the CLI enters the QA loop:

```text
Question
   |
   v
Embed Question
   |
   v
FAISS Top-K Retrieval
   |
   v
Similarity Threshold
   |
   +---- Weak Evidence ----> "I couldn't find that information in the paper."
   |
   +---- Sufficient Evidence
                 |
                 v
        LLM receives only
        retrieved excerpts
                 |
                 v
           Grounded Answer
```

### 3.2 Shared Agent State

The graph uses a typed `AgentState` in `app/graph/state.py`.

The state can contain:

* `user_query`
* `query_type`
* `candidate_papers`
* `paper_id`
* `paper_metadata`
* `pdf_url`
* `pdf_path`
* Parsed text and abstract
* Page information
* Page/character statistics
* Chunks
* Vector-store and metadata paths
* Generated briefing
* Current QA question
* Retrieved chunks
* Answer
* Sources
* Conversation history
* Status/error information

This makes intermediate artifacts explicit and allows each node to perform one responsibility.

---

## 4. Node Responsibilities

### 4.1 Query Understanding

**Node:** `understand_query`

Determines whether the input is:

* A direct arXiv paper identifier or URL
* A research topic
* Invalid input

Examples:

```text
1706.03762

https://arxiv.org/abs/1706.03762

recent work on retrieval augmented generation evaluation
```

### 4.2 arXiv Retrieval

**Node:** `search_arxiv`

For topic input, the system calls the official arXiv Atom API.

The project does not scrape arXiv webpages.

Metadata includes:

* Title
* Authors
* Abstract
* arXiv ID
* Publication date
* Categories
* PDF URL
* Abstract URL

### 4.3 Candidate Selection

**Node:** `select_paper`

For topic searches, multiple candidates may be returned.

The ranking stage combines semantic relevance between the query and the paper's title/abstract with a small recency component.

The top candidates are retained in state, and the selected paper is passed to the ingestion pipeline.

If arXiv returns no candidates, the graph stops safely rather than inventing a paper.

### 4.4 Direct Paper Lookup

**Node:** `get_direct_paper`

For a specific arXiv ID or URL, the system skips candidate search and retrieves that paper's metadata directly from arXiv.

### 4.5 PDF Fetch

**Node:** `fetch_pdf`

Downloads the paper PDF to:

```text
data/papers/
```

Network and download errors are converted into controlled agent failures.

### 4.6 PDF Parsing

**Node:** `parse_pdf`

Uses PyMuPDF to extract the document page by page.

The parser captures:

* Page text
* Full extracted text
* Abstract
* Page count
* Character count
* Reference-section detection

The parser also checks whether the extracted content is large enough to support reliable downstream processing.

Very low-quality extraction is treated as a failure rather than silently producing a potentially misleading briefing.

### 4.7 Chunking and Indexing

**Node:** `chunk_and_index`

The parsed pages are converted into retrieval chunks.

Default settings:

```text
CHUNK_SIZE=1400
CHUNK_OVERLAP=220
```

Each chunk retains useful metadata such as:

* Chunk ID
* Page number
* Section
* Source text

Embeddings are generated with:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The vectors are stored locally using FAISS with normalized embeddings and inner-product similarity.

No cloud vector database is required.

### 4.8 Executive Briefing

**Node:** `generate_briefing`

The LLM generates a structured briefing containing:

* Title
* Authors
* arXiv ID
* Publication date
* Link
* Why the paper matters
* Problem statement
* Method/approach
* Key results/claims
* Limitations
* Suggested follow-up questions

The briefing output is validated using a Pydantic schema.

The implementation also handles common LLM structured-output problems such as:

* Fenced JSON
* Type mismatches
* Incomplete list fields
* Empty required sections

The fallback behavior avoids inventing paper-specific facts.

### 4.9 Session Persistence

**Node:** `save_session`

Session information is persisted to:

```text
data/sessions/
```

The PDF is persisted under:

```text
data/papers/
```

The FAISS index and chunk metadata are persisted under:

```text
data/indexes/
```

The QA loop then loads the saved vector index for follow-up questions.

The active CLI maintains conversation history during the current session.

---

## 5. Grounded RAG QA

Grounding is one of the main design goals of the project.

For every QA question:

1. The question is embedded.
2. FAISS retrieves the top-K paper chunks.
3. The best similarity score is checked.
4. If evidence is below the configured threshold, the system returns:

```text
I couldn't find that information in the paper.
```

5. If sufficient evidence exists, only the retrieved paper excerpts are passed to the LLM.
6. The LLM is explicitly instructed to answer using those excerpts only.
7. Retrieved page numbers, sections, chunk IDs, and similarity scores are displayed to the user.

Default settings:

```text
TOP_K=5
QA_MIN_SIMILARITY=0.30
```

This approach does not mathematically guarantee zero hallucinations, but it makes the grounding policy explicit and testable.

A deliberately conservative threshold may sometimes produce a false negative. For this assessment, that tradeoff is preferable to confidently generating unsupported information.

---

## 6. Real End-to-End Validation

The project was tested locally using:

```text
1706.03762
```

which is:

```text
Attention Is All You Need
```

The successful run produced:

```text
[1/7] Understanding query...
[2/7] Paper selected.
[3/7] PDF downloaded.
[4/7] PDF parsed: 15 pages, 39483 extracted characters.
[5/7] Chunks and FAISS index created: 38 chunks.
[6/7] Executive briefing generated.
[7/7] QA mode ready.
```

The generated briefing included:

* Paper metadata
* Why the paper matters
* Problem statement
* Method/approach
* Key results
* Explicit limitations
* Follow-up questions

### 6.1 Grounded QA Example

**Question:**

```text
What is the Transformer architecture?
```

The system returned a detailed answer describing the encoder, decoder, multi-head self-attention, feed-forward layers, residual connections, layer normalization, masking, and model dimensions.

It also displayed retrieved sources such as:

```text
page 3, section '1', chunk_0007, similarity=0.466
page 8, section '1', chunk_0020, similarity=0.350
page 9, section '1', chunk_0023, similarity=0.340
page 5, section '1', chunk_0011, similarity=0.331
page 8, section '1', chunk_0022, similarity=0.329
```

### 6.2 Unsupported-Question Example

**Question:**

```text
What is the current market share of ChatGPT in 2026?
```

The system returned:

```text
I couldn't find that information in the paper.
```

It still displayed the retrieved chunks and their similarity scores.

This demonstrates the intended refusal behavior when the requested information is not supported by the paper.

### 6.3 Suggested Third QA Example

For the final demonstration, a useful third question is:

```text
What are the key results reported by the paper?
```

This should retrieve the paper's results section and answer using the available evidence.

---

## 7. Example CLI Interaction

```text
======================================================================
AUTONOMOUS arXiv PAPER DIGEST & QA AGENT
======================================================================
Enter a research topic, arXiv ID, or arXiv URL.

> 1706.03762

[1/7] Understanding query...
[2/7] Paper selected.
[3/7] PDF downloaded.
[4/7] PDF parsed: 15 pages, 39483 extracted characters.
[5/7] Chunks and FAISS index created: 38 chunks.
[6/7] Executive briefing generated.

======================================================================
EXECUTIVE BRIEFING
======================================================================
Title: Attention Is All You Need
Authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, ...
arXiv ID: 1706.03762
Publish date: 2017-06-12T17:57:34Z
Link: https://arxiv.org/pdf/1706.03762v7

WHY THIS PAPER MATTERS
...

PROBLEM STATEMENT
...

METHOD / APPROACH
• ...
• ...

KEY RESULTS / CLAIMS
• ...
• ...

LIMITATIONS
...

SUGGESTED FOLLOW-UP QUESTIONS
• ...
• ...

[7/7] QA mode ready.

Ask a question (or type 'exit'):
> What is the Transformer architecture?

ANSWER
...

RETRIEVED SOURCES
• page 3, section '1', chunk_0007, similarity=0.466
• page 8, section '1', chunk_0020, similarity=0.350
• ...

Ask a question (or type 'exit'):
> What is the current market share of ChatGPT in 2026?

ANSWER
I couldn't find that information in the paper.
```

---

## 8. Failure Handling

### No arXiv Results

If a vague topic returns no candidates:

```text
No relevant arXiv papers were found for this topic.
```

The graph stops safely.

### Invalid Input

Very short or malformed input is rejected instead of being sent through the full pipeline.

### arXiv/API Failure

Network and arXiv API errors are caught and converted into a controlled agent error.

The arXiv client retries transient request failures before giving up.

### PDF Download Failure

If the PDF cannot be downloaded or does not produce a valid response, the pipeline stops safely.

### Poor PDF Extraction

If a paper produces too little extracted text, the parser raises a controlled error rather than allowing the LLM to summarize unreliable content.

This is useful for scanned/image-based PDFs and incompatible layouts.

### Many Candidates

For topic searches, candidate papers are ranked before selecting the paper used for the briefing.

The CLI can display the top candidates and their selection scores.

### LLM Structured-Output Failure

Briefing generation validates the LLM output against a Pydantic schema.

Malformed JSON, fenced JSON, type mismatches, and incomplete required fields are handled explicitly.

If the briefing cannot be made reliable, the agent reports the failure instead of returning a partial misleading briefing.

### QA Failure

A QA exception is caught in the CLI and reported as:

```text
QA failed safely: ...
```

The session remains available for another question.

---

## 9. Technology Stack

| Category            | Technology                               |
| ------------------- | ---------------------------------------- |
| Language            | Python                                   |
| Agent orchestration | LangGraph                                |
| LLM provider        | Groq                                     |
| Local LLM fallback  | Ollama                                   |
| PDF processing      | PyMuPDF                                  |
| Embeddings          | Sentence Transformers                    |
| Embedding model     | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector retrieval    | FAISS                                    |
| Validation          | Pydantic                                 |
| HTTP/API            | Requests                                 |
| Testing             | pytest                                   |

---

## 10. Why These Choices?

### LangGraph

The assessment specifically asks for an explicit stateful graph rather than a monolithic prompt chain.

LangGraph makes the following visible in the implementation:

* Nodes
* Conditional routing
* Shared state
* Failure paths

The tradeoff is additional state and workflow code, but that makes the architecture easier to reason about and test.

### Official arXiv API

The project uses the official arXiv Atom API:

```text
https://export.arxiv.org/api/query
```

No webpage scraping is used.

This keeps metadata retrieval simple and aligned with the assessment requirement.

### PyMuPDF

PyMuPDF is a practical choice for normal text-based academic PDFs.

The tradeoff is that complex academic layouts can still be difficult to parse perfectly. The implementation therefore checks extraction quality rather than assuming every PDF was parsed correctly.

### Sentence Transformers + FAISS

Embeddings are generated locally and FAISS provides local vector search.

Advantages:

* No cloud vector database
* Simple deployment
* Easy local testing
* Transparent retrieval
* Page/chunk metadata can be displayed alongside results

### Groq + Ollama

The LLM provider is separated behind:

```text
app/llm/provider.py
```

Groq provides fast hosted inference when a key is configured.

Ollama provides a local alternative.

The project therefore does not require a paid API subscription.

Provider configuration:

```text
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Or:

```text
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

If `LLM_PROVIDER` is left empty, the application automatically uses Groq when a Groq key is available and otherwise attempts Ollama.

---

## 11. Setup

### Requirements

Recommended:

* Python 3.12
* Internet connection for arXiv and Groq
* Optional Ollama installation for local LLM generation

The project was validated locally with Python 3.12.

### Step 1: Create a Virtual Environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell activation is restricted, use Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional editable installation:

```bash
pip install -e .
```

---

## 12. LLM Configuration

### Option A — Groq

Copy:

```text
.env.example
```

to:

```text
.env
```

Then set:

```text
LLM_PROVIDER=groq
GROQ_API_KEY=your_actual_groq_key
GROQ_MODEL=openai/gpt-oss-120b
```

Never commit `.env` or your real API key.

The submitted ZIP should contain `.env.example`, not your real `.env`.

### Option B — Ollama

Install Ollama separately and pull a local model.

Example:

```bash
ollama pull llama3.2:3b
```

Then configure:

```text
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

No hosted LLM API key is required when using the local Ollama path.

---

## 13. Run the Application

Run:

```bash
python main.py
```

Examples:

### Specific Paper

```text
1706.03762
```

### arXiv URL

```text
https://arxiv.org/abs/1706.03762
```

### Research Topic

```text
recent work on retrieval augmented generation evaluation
```

After the briefing is generated, ask follow-up questions:

```text
Ask a question (or type 'exit'):
```

Type:

```text
exit
```

to end the session.

---

## 14. Configuration

The main configuration values are in `.env`.

```env
# LLM
LLM_PROVIDER=groq
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Retrieval
TOP_K=5
QA_MIN_SIMILARITY=0.30

# Chunking
CHUNK_SIZE=1400
CHUNK_OVERLAP=220

# arXiv
ARXIV_MAX_RESULTS=10
ARXIV_TIMEOUT=30
```

---

## 15. Testing

Run:

```bash
pytest -q
```

The current validated test suite contains:

```text
13 passed
```

The tests cover:

* Query classification and arXiv ID extraction
* Candidate ranking
* Chunking and overlap
* PDF parsing
* Briefing validation and structured-output robustness

The tests are designed to avoid requiring live LLM calls where possible.

---

## 16. Project Structure

```text
arxiv-paper-agent/
│
├── app/
│   ├── arxiv/
│   │   ├── client.py
│   │   └── ranking.py
│   │
│   ├── graph/
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── workflow.py
│   │
│   ├── ingestion/
│   │   ├── downloader.py
│   │   ├── parser.py
│   │   └── chunker.py
│   │
│   ├── llm/
│   │   ├── provider.py
│   │   ├── briefing.py
│   │   ├── qa.py
│   │   └── prompts.py
│   │
│   ├── retrieval/
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   │
│   ├── cli.py
│   └── config.py
│
├── data/
│   ├── indexes/
│   ├── papers/
│   └── sessions/
│
├── sample/
│   ├── example_run.md
│   └── assessment_mapping.md
│
├── tests/
│   ├── test_briefing.py
│   ├── test_chunking.py
│   ├── test_parser.py
│   ├── test_query.py
│   └── test_ranking.py
│
├── .env.example
├── .gitignore
├── main.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 17. Design Decisions & Tradeoffs

This project intentionally prioritizes reliability and explainability over UI polish.

The assessment explicitly states that a CLI or simple script is acceptable, so engineering effort was focused on graph/state design, correctness and grounding, and retrieval/parsing quality.

### Stateful Graph vs. Single Chain

A single prompt chain would have been smaller, but it would hide the intermediate state and make failure handling harder to reason about.

The LangGraph workflow separates:

* Query understanding
* Retrieval
* Selection
* PDF ingestion
* Parsing
* Indexing
* Briefing generation
* Persistence

This makes the system easier to test and explain.

### Simple Candidate Ranking

For topic searches, the project uses semantic similarity between the query and candidate title/abstract plus a small recency component.

This is intentionally simpler than a production search/reranking system.

With more time, I would evaluate:

* Lexical scoring
* Cross-encoder reranking
* Citation/author signals
* Multi-paper synthesis

### Conservative PDF Parsing

Academic PDFs can contain:

* Two-column layouts
* Equations
* Tables
* Figures
* Scanned pages
* Unusual formatting

The project chooses to fail clearly when extracted text is too sparse rather than silently producing an unreliable briefing.

With more time, I would add OCR and stronger layout-aware parsing.

### Conservative RAG

The QA stage uses:

* Top-K retrieval
* Similarity thresholding
* Source metadata
* Context-only prompting

The system may sometimes refuse a question even when a human could infer the answer from a weakly related passage.

That is an intentional tradeoff: for this assessment, a safe refusal is preferable to an unsupported confident answer.

### LLM Provider Abstraction

The application does not hard-code the entire system around one LLM provider.

Groq is convenient for hosted testing, while Ollama gives a local path.

This adds a small abstraction layer but improves portability.

---

## 18. Known Limitations

### PDF Layout Complexity

PyMuPDF works well for normal text PDFs but does not fully reconstruct every academic layout.

### Scanned PDFs

Image-only papers are not OCR'd. The parser instead detects insufficient extracted text and fails safely.

### Candidate Ranking

Topic ranking is intentionally lightweight and is not a production-grade scholarly search engine.

### RAG Threshold Sensitivity

`QA_MIN_SIMILARITY` can trade recall for precision. A threshold that is too high can cause unnecessary refusals.

### LLM Variability

Different LLMs can produce different briefing wording and QA responses. Structured validation and prompts reduce this variability but cannot eliminate it.

### Session Persistence Scope

The initial graph state, vector index, metadata, and session information are persisted. The active CLI maintains QA conversation history in memory during the current run. A more complete implementation could persist every subsequent QA turn to the session file.

### Single-Paper Workflow

The current implementation selects one paper for a topic query rather than synthesizing multiple papers.

---

## 19. What I Would Improve With More Time

If this were extended beyond the assessment scope, I would prioritize:

* Cross-encoder reranking for topic search and QA retrieval
* Better academic section detection
* OCR fallback for scanned PDFs
* Sentence-level citations in generated answers
* Multi-paper comparison and synthesis
* A formal retrieval/faithfulness evaluation dataset
* Persistent multi-turn QA sessions
* More detailed observability and structured logs
* Better handling of tables, figures, equations, and references
* More provider options for local and hosted models

---

## Conclusion

The project is intentionally a small, explainable arXiv research agent rather than a large production platform.

The main design priorities are:

```text
explicit state
      ↓
reliable ingestion
      ↓
local retrieval
      ↓
structured briefing
      ↓
grounded QA
      ↓
safe refusal
```

This keeps the implementation aligned with the assessment while leaving clear paths for future improvements.
