from app.arxiv.client import extract_arxiv_id, is_specific_paper
from app.graph.nodes import understand_query

def test_extract_id():
    assert extract_arxiv_id("2401.12345") == "2401.12345"
    assert extract_arxiv_id("https://arxiv.org/abs/2401.12345") == "2401.12345"
    assert extract_arxiv_id("https://arxiv.org/pdf/2401.12345.pdf") == "2401.12345"

def test_query_understanding():
    assert understand_query({"user_query": "2401.12345"})["query_type"] == "paper_id"
    assert understand_query({"user_query": "recent work on RAG"})["query_type"] == "topic"

def test_invalid_query():
    result = understand_query({"user_query": "x"})
    assert result["status"] == "failed"
