# Autonomous arXiv Paper Digest & QA Agent
A stateful AI research agent built for the AI Intern assessment.
The agent accepts a natural-language research topic, an arXiv ID, or an arXiv URL. It retrieves the paper, parses the PDF, creates a local
FAISS vector index, generates a structured executive briefing, and provides grounded follow-up question answering.
The project focuses on explicit agent state, reliable retrieval and parsing, grounded RAG, safe refusal of unsupported questions, failure
handling, and explainable engineering decisions.
---
1. What the Project Does
User Input
    |
    v
Query Understanding
    |
    +-------------------------+
    |                         |
  Topic                 arXiv ID / URL
    |                         |
    v                         v
arXiv Search            Direct Lookup
    |                         |
    v                         |
Candidate Ranking             |
    +------------+------------+
                 |
                 v
            Fetch PDF
                 |
                 v
            Parse PDF
             PyMuPDF
                 |
                 v
             Chunking
                 |
                 v
       Sentence Transformers
                 |
                 v
             FAISS
                 |
                 v
       Executive Briefing
                 |
                 v
              QA Mode
                 |
                 v
          Top-K Retrieval
                 |
                 v
           Grounded LLM
The workflow is implemented as an explicit LangGraph `StateGraph` rather than a single monolithic prompt.
2. Key Features
 Natural-language topic search
 Direct arXiv ID or URL input
 Official arXiv API retrieval
 Candidate paper ranking
 PDF downloading and parsing
 Page and section metadata
 Local embeddings using Sentence Transformers
 Local FAISS vector search
 Structured executive briefing
 Pydantic validation
 Grounded RAG-based QA
 Similarity-based refusal of unsupported questions
 Retrieved source/page information
 Session and vector-store persistence
 Explicit failure handling
 Automated pytest suite
 Groq LLM support
 Ollama local LLM fallback
 CLI interface
3. LangGraph Architecture
START
  |
  v
understand_query
  |
  +--------------------+
  |                    |
 topic                direct
  |                    |
  v                    v
search_arxiv      get_direct_paper
  |
  v
select_paper
  |
  v
fetch_pdf
  |
  v
parse_pdf
  |
  v
chunk_and_index
  |
  v
generate_briefing
  |
  v
save_session
  |
  v
END
| Node | Responsibility |
|---|---|
| `understand_query` | Identifies topic, arXiv ID/URL, or invalid input |
| `search_arxiv` | Searches the official arXiv API |
| `select_paper` | Ranks and selects a candidate |
| `get_direct_paper` | Retrieves a specific arXiv paper |
| `fetch_pdf` | Downloads the PDF |
| `parse_pdf` | Extracts text and document metadata |
| `chunk_and_index` | Creates chunks, embeddings and FAISS index |
| `generate_briefing` | Generates and validates the briefing |
| `save_session` | Persists session information |
4. Shared Agent State
The workflow uses a typed `AgentState`.
The state can contain:
 User query and query type
 Candidate papers and selected paper ID
 Paper metadata and PDF path
 Parsed text and abstract
 Page information and extraction statistics
 Chunks and vector-store metadata
 Generated briefing
 Current QA question and retrieved chunks
 Answer and sources
 Conversation history
 Status and error information
This makes intermediate results explicit and allows each node to perform one responsibility.
5. Retrieval and PDF Processing
arXiv
Topic searches use the official arXiv Atom API rather than webpage scraping.
Metadata includes title, authors, abstract, arXiv ID, publication date, categories and PDF URL.
PDF Parsing
PyMuPDF extracts page text, full text, abstract, page count, character count and reference-section information. Extraction quality is
checked so poor PDFs fail safely.
Chunking
CHUNK_SIZE=1400
CHUNK_OVERLAP=220
Chunks retain chunk ID, page number, section and source text.
Embeddings
sentence-transformers/all-MiniLM-L6-v2
Vector Search
FAISS provides local vector search using normalized embeddings and inner-product similarity. No cloud vector database is required.
6. Executive Briefing
The generated briefing contains:
 Title
 Authors
 arXiv ID
 Publication date
 Paper link
 Why the paper matters
 Problem statement
 Method / approach
 Key results / claims
 Limitations
 Suggested follow-up questions
The LLM output is validated using Pydantic. Common structured-output issues such as malformed JSON, fenced JSON, type mismatches
and incomplete fields are handled explicitly.
7. Grounded RAG QA
For every question:
Question
   |
   v
Create embedding
   |
   v
FAISS Top-K Retrieval
   |
   v
Similarity Check
   |
   +--------------------------+
   |                          |
 Weak Evidence          Sufficient Evidence
   |                          |
   v                          v
Safe Refusal            Retrieved Context
                              |
                              v
                         Grounded LLM
                              |
                              v
                           Answer
Default settings:
TOP_K=5
QA_MIN_SIMILARITY=0.30
If evidence is too weak:
I couldn't find that information in the paper.
When evidence is sufficient, only retrieved paper excerpts are passed to the LLM. Retrieved page, section, chunk ID and similarity
information can be displayed.
8. Example QA
Supported question:
What is the Transformer architecture?
The system retrieves relevant paper sections and generates an answer using the evidence.
Unsupported question:
What is the current market share of ChatGPT in 2026?
Expected behavior:
I couldn't find that information in the paper.
This prevents unsupported information from being presented as if it came from the paper.
9. Failure Handling
The application handles:
 Invalid or malformed input
 No arXiv search results
 arXiv/API failures
 PDF download failures
 Poor PDF extraction
 Empty or invalid indexing
 LLM structured-output failures
 Weak QA evidence
 QA runtime errors
If no usable paper is found:
No relevant arXiv papers were found for this topic.
The graph stops instead of inventing a result.
10. Technology Stack
| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Agent orchestration | LangGraph |
| Hosted LLM | Groq |
| Local LLM | Ollama |
| Paper retrieval | Official arXiv API |
| PDF processing | PyMuPDF |
| Embeddings | Sentence Transformers |
| Vector search | FAISS |
| Validation | Pydantic |
| HTTP | Requests |
| Testing | pytest |
| Interface | CLI |
No paid API is required. Groq can be used for hosted inference, while Ollama provides a local alternative.
11. Why These Choices?
LangGraph: makes nodes, routing, shared state and failure paths explicit.
Official arXiv API: provides structured metadata without webpage scraping.
PyMuPDF: provides practical local PDF extraction; extraction quality is checked.
Sentence Transformers + FAISS: provides local semantic retrieval without a cloud vector database.
Groq + Ollama: separates the LLM provider from the core workflow and provides both hosted and local options.
Conservative RAG: combines retrieval, similarity thresholding, context-only prompting and safe refusal.
12. Setup
Requirements:
 Python 3.12 recommended
 Internet connection for arXiv
 Groq API key OR Ollama
 Git
Clone:
git clone https://github.com/YOUR_USERNAME/autonomous-arxiv-paper-digest-qa-agent.git
cd autonomous-arxiv-paper-digest-qa-agent
Create a virtual environment:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
If PowerShell activation is restricted:
python -m venv .venv
.venv\Scripts\activate
Install:
python -m pip install --upgrade pip
pip install -r requirements.txt
Optional:
pip install -e .
13. LLM Configuration
Groq
Copy `.env.example` to `.env` and configure:
LLM_PROVIDER=groq
GROQ_API_KEY=your_actual_groq_key
GROQ_MODEL=openai/gpt-oss-120b
Never commit `.env` or the real API key.
Ollama
Install Ollama and pull a model:
ollama pull llama3.2:3b
Configure:
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
No hosted API key is required when using Ollama.
14. Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
TOP_K=5
QA_MIN_SIMILARITY=0.30
CHUNK_SIZE=1400
CHUNK_OVERLAP=220
ARXIV_MAX_RESULTS=10
ARXIV_TIMEOUT=30
15. Run the Application
python main.py
Examples:
arXiv ID
1706.03762
arXiv URL
https://arxiv.org/abs/1706.03762
Research Topic
recent work on retrieval augmented generation evaluation
After the briefing, QA mode starts:
Ask a question (or type 'exit'):
Type `exit` to end the session.

16. Example End-to-End Validation
The project was validated using:
1706.03762
which is:
Attention Is All You Need
Successful run:
[1/7] Understanding query...
[2/7] Paper selected.
[3/7] PDF downloaded.
[4/7] PDF parsed: 15 pages, 39483 extracted characters.
[5/7] Chunks and FAISS index created: 38 chunks.
[6/7] Executive briefing generated.
[7/7] QA mode ready.
The briefing included paper metadata, problem, method, results, limitations and follow-up questions.
17. Testing
Run:
pytest -q
Validated result:
13 passed
Tests cover query classification, arXiv ID extraction, candidate ranking, chunking, chunk overlap, PDF parsing, briefing validation and
structured-output robustness.
The tests minimize live LLM calls where possible.
18. Project Structure
autonomous-arxiv-paper-digest-qa-agent/
■
■■■ app/
■   ■■■ arxiv/
■   ■   ■■■ client.py
■   ■   ■■■ ranking.py
■   ■■■ graph/
■   ■   ■■■ state.py
■   ■   ■■■ nodes.py
■   ■   ■■■ workflow.py
■   ■■■ ingestion/
■   ■   ■■■ downloader.py
■   ■   ■■■ parser.py
■   ■   ■■■ chunker.py
■   ■■■ llm/
■   ■   ■■■ provider.py
■   ■   ■■■ briefing.py
■   ■   ■■■ qa.py
■   ■   ■■■ prompts.py
■   ■■■ retrieval/
■   ■   ■■■ embeddings.py
■   ■   ■■■ vector_store.py
■   ■■■ cli.py
■   ■■■ config.py
■
■■■ data/
■   ■■■ indexes/
■   ■■■ papers/
■   ■■■ sessions/
■■■ sample/
■   ■■■ example_run.md
■   ■■■ assessment_mapping.md
■■■ tests/
■   ■■■ test_briefing.py
■   ■■■ test_chunking.py
■   ■■■ test_parser.py
■   ■■■ test_query.py
■   ■■■ test_ranking.py
■■■ .env.example
■■■ .gitignore
■■■ main.py
■■■ pyproject.toml
■■■ requirements.txt
■■■ README.md


19. Persistence
Generated artifacts are stored locally:
data/papers/
Downloaded PDFs.
data/indexes/
FAISS indexes and chunk metadata.
data/sessions/
Session information and generated results.
The active CLI maintains QA conversation history during the current run.
20. Design Tradeoffs
Stateful graph vs. simple chain: a single chain would be smaller, but LangGraph makes state, routing and responsibilities visible.
Lightweight ranking: topic ranking uses semantic relevance and a small recency component rather than a production scholarly ranking
system.
Conservative PDF parsing: the system fails safely when extraction quality is too low.
Conservative RAG: a threshold can occasionally cause a refusal when weak evidence exists; this favors grounded responses.
Single-paper workflow: topic searches currently select one paper rather than performing multi-paper synthesis.
21. Known Limitations
 Complex academic PDF layouts may not parse perfectly.
 Scanned/image-only PDFs are not OCR'd.
 Topic ranking is intentionally lightweight.
 Retrieval threshold affects recall and precision.
 Different LLMs may produce different wording.
 The workflow focuses on one selected paper.
 Active QA history is maintained during the current CLI session.
22. Future Improvements
 Cross-encoder reranking
 Better academic section detection
 OCR for scanned papers
 Sentence-level citations
 Multi-paper comparison and synthesis
 Persistent multi-turn QA
 Retrieval/faithfulness evaluation datasets
 Better logging and observability
 Improved handling of tables, figures and equations
23. Assessment Alignment
| Assessment Area | Project Implementation |
|---|---|
| Agent / Graph Design | LangGraph nodes, routing and shared state |
| Correctness & Grounding | Top-K retrieval, similarity threshold and context-only QA |
| Retrieval & Parsing | Official arXiv API, PyMuPDF, chunking, embeddings and FAISS |
| Code Quality | Modular structure, typed state, error handling and tests |
| Communication | README, example run, design decisions and video |
The implementation intentionally avoids unnecessary out-of-scope features such as a full frontend, authentication, production deployment,
non-arXiv sources and model fine-tuning.

24. Summary
The project implements:
Query
  ↓
Understand
  ↓
Retrieve
  ↓
Select
  ↓
Download
  ↓
Parse
  ↓
Chunk
  ↓
Embed
  ↓
Index
  ↓
Generate Briefing
  ↓
Retrieve Evidence
  ↓
Grounded QA
  ↓
Safe Refusal

