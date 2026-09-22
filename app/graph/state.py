from typing import TypedDict, Any

class AgentState(TypedDict, total=False):
    user_query: str
    query_type: str

    candidate_papers: list[dict[str, Any]]
    paper_id: str
    paper_metadata: dict[str, Any]
    pdf_url: str
    pdf_path: str

    parsed_text: str
    abstract: str
    pages: list[dict[str, Any]]
    page_count: int
    character_count: int
    has_references_section: bool

    chunks: list[dict[str, Any]]
    vector_store_path: str
    metadata_path: str

    briefing: dict[str, Any]

    question: str
    retrieved_chunks: list[dict[str, Any]]
    answer: str
    sources: list[dict[str, Any]]
    conversation_history: list[dict[str, str]]

    status: str
    error: str
