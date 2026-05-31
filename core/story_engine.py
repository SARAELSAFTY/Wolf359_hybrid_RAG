"""
Story Summarisation Engine.

Handles general queries about plot, episodes, characters, and themes.
Uses Llama-3.1-8B for efficient summarisation.
"""

from core.retrieval import retriever
from core.prompts import format_story_prompt
from services.llm_service import generate, stream_generate
<<<<<<< HEAD
=======
from services.memory_service import memory_manager

>>>>>>> ed00e0d (Replace old files with new versions)

class StoryEngine:
    """Process story-mode queries through the retrieval → prompt → LLM pipeline."""

<<<<<<< HEAD
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
=======
    def handle_query(self, query_embedding, query_text: str, session_id: str = "default") -> str:
>>>>>>> ed00e0d (Replace old files with new versions)
        """
        Process a story query end-to-end (non-streaming).

        Args:
            query_embedding: The query vector (768-dim numpy array).
            query_text: The raw user question.
<<<<<<< HEAD
=======
            session_id: Unique session identifier for memory management.
>>>>>>> ed00e0d (Replace old files with new versions)

        Returns:
            The LLM response as a string.
        """
<<<<<<< HEAD
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
=======
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
>>>>>>> ed00e0d (Replace old files with new versions)

    def _build_context(self, results: list[dict]) -> list[dict]:
        """Convert retrieval results into context dicts for prompt assembly."""
        context = []
<<<<<<< HEAD
        for r in results:
            doc_id = r["doc_id"]
            # Use the sub-chunk text returned directly by the retriever
            text = r.get("text", f"[Episode: {doc_id}]")
            
            context.append(
                {
                    "doc_id": doc_id,
=======
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
>>>>>>> ed00e0d (Replace old files with new versions)
                    "text": text,
                    "score": r.get("score", 0.0),
                }
            )
        return context


# Module-level singleton
<<<<<<< HEAD
story_engine = StoryEngine()

=======
story_engine = StoryEngine()
>>>>>>> ed00e0d (Replace old files with new versions)
