"""
Story Summarisation Engine.

Handles general queries about plot, episodes, characters, and themes.
Uses Llama-3.1-8B for efficient summarisation.
"""

from core.retrieval import retriever
from core.prompts import format_story_prompt
from services.llm_service import generate, stream_generate

class StoryEngine:
    """Process story-mode queries through the retrieval → prompt → LLM pipeline."""

    def __init__(self):
        # We no longer need to load all scripts, we use chunk text
        pass

    def _get_available_episodes(self) -> list[str]:
        if not hasattr(self, '_available_episodes'):
            # Get unique episodes from chunk metadata
            unique_eps = sorted(list(set(entry["doc_id"] for entry in retriever.metadata)))
            self._available_episodes = unique_eps
        return self._available_episodes

    def handle_query(self, query_embedding, query_text: str) -> str:
        """
        Process a story query end-to-end (non-streaming).

        Args:
            query_embedding: The query vector (768-dim numpy array).
            query_text: The raw user question.

        Returns:
            The LLM response as a string.
        """
        # Retrieve relevant context
        results = retriever.retrieve(query_embedding, mode="story")

        # Build context chunk dicts for prompt
        context_chunks = self._build_context(results)

        # Assemble prompt
        messages = format_story_prompt(query_text, context_chunks, self._get_available_episodes())

        # Generate response
        return generate(messages, mode="story")

    def handle_query_stream(self, query_embedding, query_text: str):
        """
        Process a story query with streaming response.

        Yields:
            str: Response token chunks as they arrive from the LLM.
        """
        results = retriever.retrieve(query_embedding, mode="story")
        context_chunks = self._build_context(results)
        messages = format_story_prompt(query_text, context_chunks, self._get_available_episodes())
        yield from stream_generate(messages, mode="story")

    def _build_context(self, results: list[dict]) -> list[dict]:
        """Convert retrieval results into context dicts for prompt assembly."""
        context = []
        for r in results:
            doc_id = r["doc_id"]
            # Use the sub-chunk text returned directly by the retriever
            text = r.get("text", f"[Episode: {doc_id}]")
            
            context.append(
                {
                    "doc_id": doc_id,
                    "text": text,
                    "score": r.get("score", 0.0),
                }
            )
        return context


# Module-level singleton
story_engine = StoryEngine()

