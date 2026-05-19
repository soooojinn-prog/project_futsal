from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from rag.claude_client import ClaudeClient

from .nodes import (
    parse_intent,
    single_match_node,
    single_review_node,
    single_stadium_node,
    single_team_node,
    summarize_node,
    tournament_assemble_node,
)
from .state import AgentState
from .tools import Tools


def _route_after_parse(state: AgentState) -> str:
    if state["intent"] == "TOURNAMENT":
        return "tournament_assemble"
    if state["intent"] == "SINGLE":
        return "single_stadium"
    return "summarize"  # UNKNOWN — 바로 요약 (에러 응답)


def build_agent_graph(claude_client: ClaudeClient, tools: Tools):
    g: StateGraph = StateGraph(AgentState)

    g.add_node("parse_intent", lambda s: parse_intent(s, claude_client=claude_client))
    g.add_node("single_stadium", lambda s: single_stadium_node(s, tools=tools))
    g.add_node("single_team", lambda s: single_team_node(s, tools=tools))
    g.add_node("single_match", lambda s: single_match_node(s, tools=tools))
    g.add_node("single_review", lambda s: single_review_node(s, tools=tools))
    g.add_node(
        "tournament_assemble", lambda s: tournament_assemble_node(s, tools=tools)
    )
    g.add_node("summarize", summarize_node)

    g.add_edge(START, "parse_intent")
    g.add_conditional_edges(
        "parse_intent",
        _route_after_parse,
        {
            "single_stadium": "single_stadium",
            "tournament_assemble": "tournament_assemble",
            "summarize": "summarize",
        },
    )
    g.add_edge("single_stadium", "single_team")
    g.add_edge("single_team", "single_match")
    g.add_edge("single_match", "single_review")
    g.add_edge("single_review", "summarize")
    g.add_edge("tournament_assemble", "summarize")
    g.add_edge("summarize", END)

    return g.compile()
