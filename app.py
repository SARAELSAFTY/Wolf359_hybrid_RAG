import sys
from pathlib import Path

# Ensure project root is on sys.path for relative imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import streamlit as st

from config import GROQ_API_KEY, HF_KEY
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
    if "character_embedding" not in st.session_state:
        st.session_state.character_embedding = None


# ------------------------------------------------------------------
# Query embedding helper
# ------------------------------------------------------------------
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

def embed_query(query_text: str) -> np.ndarray:
    """Generate a semantic embedding using HuggingFace API."""
    if not HF_KEY:
        st.error("HuggingFace API key not configured. Add HF_API_KEY to .env")
        st.stop()
    
    api_url = "https://router.huggingface.co/hf-inference/models/BAAI/bge-base-en-v1.5/pipeline/feature-extraction"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    
    # BGE models require instruction prefix for queries
    instruction_query = f"Represent this sentence: {query_text}"
    
    # Configure resilient session with retries for network drops
    session = requests.Session()
    retries = Retry(
        total=3, 
        backoff_factor=1, 
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    try:
        response = session.post(
            api_url,
            headers=headers,
            json={"inputs": instruction_query, "options": {"wait_for_model": True}},
            timeout=15
        )
    except requests.exceptions.ConnectionError:
        st.error("Network Error: Failed to resolve or connect to Hugging Face. Check your internet, DNS, or VPN settings.")
        st.stop()
    except requests.exceptions.Timeout:
        st.error("Timeout Error: The request to Hugging Face timed out. Please try again.")
        st.stop()
    
    if response.status_code != 200:
        st.error(f"HuggingFace API error: {response.status_code} - {response.text}")
        st.stop()
    
    embedding = np.array(response.json(), dtype="float32")
    return embedding
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
    
    if not HF_KEY:
        st.error(
            "⚠️ **HuggingFace API key not configured.** "
            "Please add your API key to the `.env` file:\n\n"
            "```\nHF_KEY=hf_your_key_here\n```"
        )
        st.stop()

    # Mode selector
    mode = render_mode_selector()

    # Handle mode switch — clear chat if mode changed
    if mode != st.session_state.mode:
        st.session_state.mode = mode
        st.session_state.messages = []
        st.session_state.character_embedding = None
        st.rerun()

    # Sidebar
    exchange_count = memory_manager.get_exchange_count(
        st.session_state.session_id
    )
    sidebar_action = render_sidebar(
        mode=mode,
        exchange_count=memory_manager.get_exchange_count(st.session_state.session_id),
        story_exchange_count=memory_manager.get_story_exchange_count(st.session_state.session_id),
    )

    if sidebar_action == "clear_history":
        memory_manager.clear_session(st.session_state.session_id)
        st.session_state.character_embedding = None
        st.rerun()
    elif sidebar_action == "clear_story_history":
        memory_manager.clear_story_session(st.session_state.session_id)
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
        if mode == "story":
            query_emb = embed_query(user_input)
        else:
            if st.session_state.character_embedding is None:
                query_emb = embed_query(user_input)
                st.session_state.character_embedding = query_emb
            else:
                query_emb = st.session_state.character_embedding

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
                        query_emb, user_input,st.session_state.session_id,
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
