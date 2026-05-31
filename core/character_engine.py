"""
Character Engine — Doug Eiffel Persona.

Manages Doug Eiffel role-play interactions using the 70B model,
conversation memory, and Doug-filtered retrieval.
"""

from core.retrieval import retriever
from core.prompts import format_doug_prompt
from services.llm_service import generate, stream_generate
from services.memory_service import memory_manager


class CharacterEngine:
    """Process character-mode queries through the retrieval → memory → prompt → LLM pipeline."""
    
    def __init__(self):
        pass

    def handle_query_stream(
        self,
        query_embedding,
        query_text: str,
        session_id: str,
    ):
        """
        Process a character query with streaming response.

        Yields:
            str: Response token chunks as they arrive.

        After streaming completes, the full response is stored in memory.
        """
        results = retriever.retrieve(query_embedding, query_text=query_text, mode="character")
        context_chunks = self._build_context(results)
        history = memory_manager.get_history(session_id)
        
        # Assemble prompt (now returns a list of messages)
        messages = format_doug_prompt(query_text, context_chunks, history)

        # Accumulate full response while streaming
        full_response = []
        for token in stream_generate(messages, mode="character"):
            full_response.append(token)
            yield token

        # Store the complete exchange in memory
        memory_manager.add_message(
            session_id, query_text, "".join(full_response)
        )

    def _build_context(self, results: list[dict]) -> list[dict]:
        """Convert retrieval results into context dicts for prompt assembly.

        Chunks with missing or empty text are skipped with a logged warning
        rather than injecting a placeholder that would cause the LLM to
        hallucinate.
        """
        import logging
        logger = logging.getLogger(__name__)

        context = []
        for r in results:
            text = r.get("text", "")
            if not text or not text.strip():
                logger.warning(
                    "Skipping chunk with empty text — episode_id=%s, chunk_index=%s",
                    r.get("episode_id", "?"),
                    r.get("chunk_index", "?"),
                )
                continue
            context.append(
                {
                    "episode_id": r["episode_id"],
                    "text": text,
                    "score": r.get("score", 0.0),
                }
            )
        return context


# Module-level singleton
character_engine = CharacterEngine()
