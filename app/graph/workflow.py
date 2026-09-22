from langgraph.graph import StateGraph, START, END
from app.graph.state import AgentState
from app.graph.nodes import (
    understand_query, search_arxiv_node, select_paper_node,
    get_direct_paper_node, fetch_pdf_node, parse_pdf_node,
    chunk_and_index_node, briefing_node, save_session,
)

def route_after_understanding(state):
    if state.get("status") == "failed":
        return "end"
    return "topic" if state.get("query_type") == "topic" else "direct"

def route_after_stage(state):
    return "end" if state.get("status") == "failed" else "continue"

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("understand_query", understand_query)
    graph.add_node("search_arxiv", search_arxiv_node)
    graph.add_node("select_paper", select_paper_node)
    graph.add_node("get_direct_paper", get_direct_paper_node)
    graph.add_node("fetch_pdf", fetch_pdf_node)
    graph.add_node("parse_pdf", parse_pdf_node)
    graph.add_node("chunk_and_index", chunk_and_index_node)
    graph.add_node("generate_briefing", briefing_node)
    graph.add_node("save_session", save_session)

    graph.add_edge(START, "understand_query")

    graph.add_conditional_edges(
        "understand_query",
        route_after_understanding,
        {"topic": "search_arxiv", "direct": "get_direct_paper", "end": END},
    )

    graph.add_conditional_edges(
        "search_arxiv", route_after_stage,
        {"continue": "select_paper", "end": END},
    )
    graph.add_conditional_edges(
        "select_paper", route_after_stage,
        {"continue": "fetch_pdf", "end": END},
    )
    graph.add_conditional_edges(
        "get_direct_paper", route_after_stage,
        {"continue": "fetch_pdf", "end": END},
    )
    graph.add_conditional_edges(
        "fetch_pdf", route_after_stage,
        {"continue": "parse_pdf", "end": END},
    )
    graph.add_conditional_edges(
        "parse_pdf", route_after_stage,
        {"continue": "chunk_and_index", "end": END},
    )
    graph.add_conditional_edges(
        "chunk_and_index", route_after_stage,
        {"continue": "generate_briefing", "end": END},
    )
    graph.add_conditional_edges(
        "generate_briefing", route_after_stage,
        {"continue": "save_session", "end": END},
    )
    graph.add_edge("save_session", END)

    return graph.compile()
