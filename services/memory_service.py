"""
Session-based conversation memory for character mode.

Uses a simple sliding window buffer backed by LangChain message types.
Memory is ephemeral — lives only in the application runtime.
"""

from collections import deque
from langchain_core.messages import HumanMessage, AIMessage
from config import MEMORY_WINDOW_SIZE


class MemoryManager:
    """
    Manages session-based conversation memory for character mode.

    Keeps a sliding window of the last N exchanges per session.
    Memory is never persisted to disk.
    """

    def __init__(self):
        self._sessions: dict[str, deque] = {}

    def _get_or_create(self, session_id: str) -> deque:
        """Get existing memory for session, or create a new one."""
        if session_id not in self._sessions:
            # Each item in the deque is a (HumanMessage, AIMessage) pair
            self._sessions[session_id] = deque(maxlen=MEMORY_WINDOW_SIZE)
        return self._sessions[session_id]

    def add_message(self, session_id: str, user_input: str, ai_response: str):
        """Store a user/assistant exchange in the session memory."""
        buf = self._get_or_create(session_id)
        buf.append((HumanMessage(content=user_input), AIMessage(content=ai_response)))

    def get_history(self, session_id: str) -> list[dict]:
        """
        Return the conversation history as a list of dicts.

        Each dict has keys 'role' ('user' or 'assistant') and 'content'.
        """
        buf = self._get_or_create(session_id)
        history = []
        for human_msg, ai_msg in buf:
            history.append({"role": "user", "content": human_msg.content})
            history.append({"role": "assistant", "content": ai_msg.content})
        return history

    def clear_session(self, session_id: str):
        """Delete all memory for a given session."""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def get_exchange_count(self, session_id: str) -> int:
        """Return the number of stored exchanges for the session."""
        buf = self._get_or_create(session_id)
        return len(buf)


# Module-level singleton
memory_manager = MemoryManager()
