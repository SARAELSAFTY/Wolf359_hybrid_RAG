"""
Session-based conversation memory for character mode and story mode.

Uses a simple sliding window buffer backed by LangChain message types.
Memory is ephemeral — lives only in the application runtime.
"""

from collections import deque
from langchain_core.messages import HumanMessage, AIMessage
from config import MEMORY_WINDOW_SIZE, STORY_MEMORY_WINDOW_SIZE


class MemoryManager:
    """
    Manages session-based conversation memory for both character and story mode.

    Keeps a sliding window of the last N exchanges per session.
    Character and story memories are stored separately.
    Memory is never persisted to disk.
    """

    def __init__(self):
        self._sessions: dict[str, deque] = {}         # character mode
        self._story_sessions: dict[str, deque] = {}   # story mode

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _get_or_create(self, session_id: str) -> deque:
        """Get existing character memory for session, or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = deque(maxlen=MEMORY_WINDOW_SIZE)
        return self._sessions[session_id]

    def _get_or_create_story(self, session_id: str) -> deque:
        """Get existing story memory for session, or create a new one."""
        if session_id not in self._story_sessions:
            self._story_sessions[session_id] = deque(maxlen=STORY_MEMORY_WINDOW_SIZE)
        return self._story_sessions[session_id]

    # ------------------------------------------------------------------ #
    #  Character mode                                                      #
    # ------------------------------------------------------------------ #

    def add_message(self, session_id: str, user_input: str, ai_response: str):
        """Store a user/assistant exchange in the character session memory."""
        buf = self._get_or_create(session_id)
        buf.append((HumanMessage(content=user_input), AIMessage(content=ai_response)))

    def get_history(self, session_id: str) -> list[dict]:
        """
        Return character conversation history as a list of role/content dicts.
        """
        buf = self._get_or_create(session_id)
        history = []
        for human_msg, ai_msg in buf:
            history.append({"role": "user", "content": human_msg.content})
            history.append({"role": "assistant", "content": ai_msg.content})
        return history

    def clear_session(self, session_id: str):
        """Delete all character memory for a given session."""
        self._sessions.pop(session_id, None)

    def get_exchange_count(self, session_id: str) -> int:
        """Return the number of stored character exchanges for the session."""
        return len(self._get_or_create(session_id))

    # ------------------------------------------------------------------ #
    #  Story mode                                                          #
    # ------------------------------------------------------------------ #

    def add_story_turn(self, session_id: str, user_action: str, story_response: str):
        """Store a player action / narrator response pair in story memory."""
        buf = self._get_or_create_story(session_id)
        buf.append((HumanMessage(content=user_action), AIMessage(content=story_response)))

    def get_story_history(self, session_id: str) -> list[dict]:
        """
        Return story conversation history as a list of role/content dicts.
        """
        buf = self._get_or_create_story(session_id)
        history = []
        for human_msg, ai_msg in buf:
            history.append({"role": "user", "content": human_msg.content})
            history.append({"role": "assistant", "content": ai_msg.content})
        return history

    def clear_story_session(self, session_id: str):
        """Delete all story memory for a given session."""
        self._story_sessions.pop(session_id, None)

    def get_story_exchange_count(self, session_id: str) -> int:
        """Return the number of stored story turns for the session."""
        return len(self._get_or_create_story(session_id))


# Module-level singleton
memory_manager = MemoryManager()
