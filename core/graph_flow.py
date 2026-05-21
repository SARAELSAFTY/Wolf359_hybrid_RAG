"""
LangGraph workflow for routing queries to the appropriate engine.

Routes to StoryEngine or CharacterEngine based on the user's mode selection.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END

from core.story_engine import story_engine
from core.character_engine import character_engine


# ------------------------------------------------------------------
# State schema
# ------------------------------------------------------------------
class QueryState(TypedDict):
    """State passed through the LangGraph workflow."""
    query_text: str
    query_embedding: object  # np.ndarray
    mode: str                # "story" or "character"
    session_id: str
    response: str
    response_chunks: list    # for streaming, collected tokens


# ------------------------------------------------------------------
# Node functions
# ------------------------------------------------------------------
def route_decision(state: QueryState) -> str:
    """Decide which engine to route to based on mode."""
    if state["mode"] == "character":
        return "character_node"
    return "story_node"


def story_node(state: QueryState) -> dict:
    """Process query through the story engine."""
    response = story_engine.handle_query(
        state["query_embedding"],
        state["query_text"],
    )
    return {"response": response}


def character_node(state: QueryState) -> dict:
    """Process query through the character engine."""
    response = character_engine.handle_query(
        state["query_embedding"],
        state["query_text"],
        state["session_id"],
    )
    return {"response": response}


# ------------------------------------------------------------------
# Graph construction
# ------------------------------------------------------------------
def build_workflow() -> StateGraph:
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(QueryState)

    # Add nodes
    workflow.add_node("story_node", story_node)
    workflow.add_node("character_node", character_node)

    # Conditional entry point: route based on mode
    workflow.set_conditional_entry_point(
        route_decision,
        {
            "story_node": "story_node",
            "character_node": "character_node",
        },
    )

    # Both nodes lead to END
    workflow.add_edge("story_node", END)
    workflow.add_edge("character_node", END)

    return workflow.compile()


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def route_query(
    query_text: str,
    query_embedding,
    mode: str,
    session_id: str = "default",
) -> str:
    """
    Route a query through the LangGraph workflow and return the response.

    Args:
        query_text: The user's question.
        query_embedding: The query vector (768-dim numpy array).
        mode: "story" or "character".
        session_id: Session ID for memory (character mode).

    Returns:
        The generated response string.
    """
    app = build_workflow()
    initial_state: QueryState = {
        "query_text": query_text,
        "query_embedding": query_embedding,
        "mode": mode,
        "session_id": session_id,
        "response": "",
        "response_chunks": [],
    }
    result = app.invoke(initial_state)
    return result["response"]
