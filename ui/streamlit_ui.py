"""
Reusable Streamlit UI components for the Wolf 359 Chatbot.
"""

import streamlit as st


# ------------------------------------------------------------------
# Styling
# ------------------------------------------------------------------
def inject_custom_css():
    """Inject custom CSS for a polished chat experience."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global */
        .stApp {
            font-family: 'Inter', sans-serif;
        }

        /* Header */
        .app-header {
            text-align: center;
            padding: 1.5rem 0 1rem 0;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }
        .app-header h1 {
            color: #f5f5f5;
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.5px;
        }
        .app-header p {
            color: #a0a0c0;
            font-size: 0.95rem;
            margin: 0.3rem 0 0 0;
        }

        /* Mode indicator */
        .mode-story {
<<<<<<< HEAD
            background: linear-gradient(90deg, #1a3a5c, #2a5a8c);
=======
            background: linear-gradient(90deg, #5c1a5b, #2a5a8c);
>>>>>>> ed00e0d (Replace old files with new versions)
            padding: 0.5rem 1rem;
            border-radius: 8px;
            color: #c0dcf0;
            text-align: center;
            margin-bottom: 1rem;
            font-size: 0.85rem;
        }
        .mode-character {
            background: linear-gradient(90deg, #5c3a1a, #8c5a2a);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            color: #f0dcc0;
            text-align: center;
            margin-bottom: 1rem;
            font-size: 0.85rem;
        }

        /* Chat message styling */
        .stChatMessage {
            border-radius: 12px !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f0c29, #1a1a3e);
<<<<<<< HEAD
        }
        section[data-testid="stSidebar"] .stMarkdown {
=======
            width: 350px !important;
        }
        section[data-testid="stSidebar"] .stMarkdown {

>>>>>>> ed00e0d (Replace old files with new versions)
            color: #c0c0e0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    """Render the application header."""
    st.markdown(
        """
        <div class="app-header">
            <h1>🛰️ Wolf 359 Interactive Chatbot</h1>
            <p>Hybrid RAG • Knowledge Graph • Dual-Mode AI</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Mode selector
# ------------------------------------------------------------------
def render_mode_selector() -> str:
    """
    Render the mode toggle and return the selected mode.

    Returns:
        "story" or "character"
    """
    mode_options = {
        "📖 Story Summarisation": "story",
        "🎙️ Chat with Doug Eiffel": "character",
    }
    selected_label = st.radio(
        "Select Mode",
        list(mode_options.keys()),
        horizontal=True,
        label_visibility="collapsed",
    )
    mode = mode_options[selected_label]

    if mode == "story":
        st.markdown(
            '<div class="mode-story">📖 Story Mode — Ask about episodes, characters, plot & themes</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="mode-character">🎙️ Character Mode — You\'re talking to Doug Eiffel</div>',
            unsafe_allow_html=True,
        )
    return mode


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
<<<<<<< HEAD
def render_sidebar(mode: str, exchange_count: int = 0):
=======
def render_sidebar(mode: str, exchange_count: int = 0, story_exchange_count: int = 0):
>>>>>>> ed00e0d (Replace old files with new versions)
    """Render sidebar with session info and controls."""
    with st.sidebar:
        st.markdown("## 🛰️ Wolf 359")
        st.markdown("---")

        # Session info
        st.markdown("### Session Info")
        mode_label = "📖 Story" if mode == "story" else "🎙️ Doug Eiffel"
        st.markdown(f"**Mode:** {mode_label}")

        if mode == "character":
<<<<<<< HEAD
            st.markdown(f"**Memory:** {exchange_count} / 10 exchanges")
            if st.button("🗑️ Clear Conversation", use_container_width=True):
                return "clear_history"

        st.markdown("---")

        # Help
        st.markdown("### 💡 Example Queries")
        if mode == "story":
            st.markdown(
                """
                - *"Summarise Episode 15"*
                - *"Who is Commander Minkowski?"*
                - *"What are the main themes?"*
                - *"What happens with Dr. Hilbert?"*
                """
            )
        else:
            st.markdown(
                """
                - *"How's life on the station?"*
                - *"Tell me about Minkowski"*
                - *"What do you think of Hilbert?"*
                - *"Any good music recommendations?"*
                """
            )

        st.markdown("---")

        # About
        st.markdown("### ℹ️ About")
        st.markdown(
            """
            Built with **Streamlit**, **LangGraph**,
            **FAISS**, **NetworkX**, and **Groq API**.

            Story mode uses **Llama-3.1-8B**.
            Character mode uses **Llama-3.3-70B**.
            """
        )

    return None


=======
            
            if st.button("🗑️ Clear Conversation", use_container_width=True):
                return "clear_history"
            st.caption("⚠️ (This will clear the conversation memory for this session)")

        elif mode == "story":
            
            if st.button("🗑️ Clear Story Memory", use_container_width=True):
                return "clear_story_history"   # ← caller handles this signal
            st.caption("⚠️ (This will clear the story memory for this session)")

        # ... rest of sidebar unchanged
>>>>>>> ed00e0d (Replace old files with new versions)
# ------------------------------------------------------------------
# Chat display
# ------------------------------------------------------------------
def render_chat(messages: list[dict]):
    """
    Render the chat message history.

    Each message dict should have 'role' ('user' or 'assistant')
    and 'content'.
    """
    for msg in messages:
        avatar = "🧑" if msg["role"] == "user" else "🛰️"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
<<<<<<< HEAD
=======


>>>>>>> ed00e0d (Replace old files with new versions)
