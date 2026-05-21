"""
Wolf 359 Interactive Chatbot — Main Streamlit Application.

Entry point: `streamlit run app.py`
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path for relative imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import streamlit as st

from config import GROQ_API_KEY
from ui.streamlit_ui import (
    inject_custom_css,
    render_header,
    render_mode_selector,
    render_sidebar,
    render_chat,
)
from core.story_engine import story_engine
from core.character_engine import character_engine
from core.retrieval import retriever
from services.memory_service import memory_manager


# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Wolf 359 Chatbot",
    page_icon="🛰️",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ------------------------------------------------------------------
# Session state initialisation
# ------------------------------------------------------------------
def init_session_state():
    """Initialise Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "mode" not in st.session_state:
        st.session_state.mode = "story"
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())


# ------------------------------------------------------------------
# Query embedding helper
# ------------------------------------------------------------------
@st.cache_resource
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')


def embed_query(query_text: str) -> np.ndarray:
    """Generate a semantic embedding for the user query."""
    model = get_embedding_model()
    # encode returns a numpy array
    query_emb = model.encode(query_text, convert_to_numpy=True)
    return query_emb.astype("float32")


# ------------------------------------------------------------------
# Main application
# ------------------------------------------------------------------
def main():
    init_session_state()
    inject_custom_css()
    render_header()

    # API key check
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        st.error(
            "⚠️ **Groq API key not configured.** "
            "Please add your API key to the `.env` file:\n\n"
            "```\nGROQ_API_KEY=gsk_your_key_here\n```"
        )
        st.stop()

    # Mode selector
    mode = render_mode_selector()

    # Handle mode switch — clear chat if mode changed
    if mode != st.session_state.mode:
        st.session_state.mode = mode
        st.session_state.messages = []
        st.rerun()

    # Sidebar
    exchange_count = memory_manager.get_exchange_count(
        st.session_state.session_id
    )
    sidebar_action = render_sidebar(mode, exchange_count)
    if sidebar_action == "clear_history":
        memory_manager.clear_session(st.session_state.session_id)
        st.session_state.messages = []
        st.rerun()

    # Render existing chat
    render_chat(st.session_state.messages)

    # Chat input
    user_input = st.chat_input(
        "Ask about Wolf 359..."
        if mode == "story"
        else "Talk to Doug Eiffel..."
    )

    if user_input:
        # Display user message
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        # Generate embedding
        query_emb = embed_query(user_input)

        # Generate response with streaming
        with st.chat_message("assistant", avatar="🛰️"):
            status_text = (
                "Searching scripts..."
                if mode == "story"
                else "Doug is typing..."
            )
            with st.spinner(status_text):
                if mode == "story":
                    response_stream = story_engine.handle_query_stream(
                        query_emb, user_input
                    )
                else:
                    response_stream = character_engine.handle_query_stream(
                        query_emb,
                        user_input,
                        st.session_state.session_id,
                    )

                response_text = st.write_stream(response_stream)

        st.session_state.messages.append(
            {"role": "assistant", "content": response_text}
        )


if __name__ == "__main__":
    main()
