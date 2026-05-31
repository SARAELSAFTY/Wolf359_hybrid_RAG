"""
Story Summarisation Engine.

Handles general queries about plot, episodes, characters, and themes.
Uses Llama-3.1-8B for efficient summarisation.
"""

from core.retrieval import retriever
from core.prompts import format_story_prompt
from services.llm_service import generate, stream_generate
from services.memory_service import memory_manager


class StoryEngine:
    """Process story-mode queries through the retrieval → prompt → LLM pipeline."""

    def handle_query(self, query_embedding, query_text: str, session_id: str = "default") -> str:
        """
        Process a story query end-to-end (non-streaming).

        Args:
            query_embedding: The query vector (768-dim numpy array).
            query_text: The raw user question.
            session_id: Unique session identifier for memory management.

        Returns:
            The LLM response as a string.
        """
        results = retriever.retrieve(query_embedding, query_text=query_text, mode="story")
        
        # Special handling for episode list queries
        if results and results[0].get("is_episode_list"):
            episode_list = [r["episode_id"] for r in results]
            # Format as a numbered list
            formatted_episodes = "\n".join([f"{i}. {ep}" for i, ep in enumerate(episode_list, 1)])
            response = f"I have access to {len(episode_list)} episodes:\n\n{formatted_episodes}"
            memory_manager.add_story_turn(session_id, query_text, response)
            return response
        
        context_chunks = self._build_context(results)

        # Get story conversation history
        history = memory_manager.get_story_history(session_id)

        messages = format_story_prompt(query_text, context_chunks, history)
        response = generate(messages, mode="story")

        # Store in story memory
        memory_manager.add_story_turn(session_id, query_text, response)

        return response

    def handle_query_stream(self, query_embedding, query_text: str, session_id: str = "default"):
        """
        Process a story query with streaming response.

        Args:
            query_embedding: The query vector (768-dim numpy array).
            query_text: The raw user question.
            session_id: The active session identifier from the frontend.

        Yields:
            str: Response token chunks as they arrive from the LLM.
        """
        results = retriever.retrieve(query_embedding, query_text=query_text, mode="story")
        
        # Special handling for episode list queries - return immediately
        if results and results[0].get("is_episode_list"):
            episode_list = [r["episode_id"] for r in results]
            # Format as a numbered list
            formatted_episodes = "\n".join([f"{i}. {ep}" for i, ep in enumerate(episode_list, 1)])
            response = f"I have access to {len(episode_list)} episodes:\n\n{formatted_episodes}"
            memory_manager.add_story_turn(session_id, query_text, response)
            yield response
            return
        
        context_chunks = self._build_context(results)

        history = memory_manager.get_story_history(session_id)

        messages = format_story_prompt(query_text, context_chunks, history)

        full_response = []
        for token in stream_generate(messages, mode="story"):
            full_response.append(token)
            yield token

        # Store the complete exchange in story memory
        memory_manager.add_story_turn(session_id, query_text, "".join(full_response))

    def _build_context(self, results: list[dict]) -> list[dict]:
        """Convert retrieval results into context dicts for prompt assembly."""
        context = []
        # Cap story mode chunks at 3 to prevent token overflows
        for r in results[:3]:
            text = r.get("text")
            if not text or not text.strip():
                raise ValueError(
                    f"Data Integrity Error: Chunk text is missing or empty for episode "
                    f"'{r.get('episode_id', 'Unknown')}'."
                )
            
            # Truncate overly long chunks to save tokens
            if len(text) > 1200:
                text = text[:1200] + "... [Truncated]"
                
            context.append(
                {
                    "episode_id": r["episode_id"],
                    "text": text,
                    "score": r.get("score", 0.0),
                }
            )
        return context


# Module-level singleton
story_engine = StoryEngine()
