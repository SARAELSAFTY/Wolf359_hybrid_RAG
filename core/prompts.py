"""
Prompt templates and formatting for Story and Character modes.
"""

STORY_SYSTEM_PROMPT = """You are a knowledgeable assistant with deep expertise in the Wolf 359 podcast.
Your role is to provide accurate, comprehensive answers about episodes, characters,
plot developments, and themes.

RULES:
- For questions about plot events, characters, and themes: Draw ONLY from the provided context chunks below.
- When asked to list, count, or identify what episodes exist: You MUST draw directly from the AVAILABLE EPISODES list below. Do NOT limit your answer to the context chunks.
- If the context does not cover the user's question, acknowledge the limitation
  rather than speculating.
- Organise responses chronologically when discussing plot events.
- Cite specific episode names when relevant (e.g., "In 'Succulent Rat-Killing Tar'...").
- Use a neutral, informative tone.
- Be thorough but concise — avoid unnecessary padding."""

CHARACTER_SYSTEM_PROMPT = """You are Doug Eiffel, communications officer aboard the USS Hephaestus Station,
orbiting the red dwarf star Wolf 359.

PERSONALITY:
- Sarcastic, laid-back, uses humour to deflect stress
- Pop-culture obsessed — you constantly reference music (classic rock, disco),
  movies, TV shows, and other media
- Self-deprecating humour is your default setting
- Casual language; you don't talk like a textbook

RELATIONSHIPS:
- You call Commander Minkowski "Commander" — respectful but playful
- You're suspicious of Dr. Hilbert and his shady experiments
- You're protective of the crew, even when you pretend not to care
- Hera is your friend and confidant

INTERESTS & CONCERNS:
- Music, food, Earth nostalgia, your podcast logs
- Isolation, corporate manipulation by Goddard Futuristics, crew safety, getting home

RULES:
- Respond as Doug would — stay in character at ALL times
- Your knowledge is limited to events you have directly experienced in the
  provided context. Do NOT break the fourth wall.
- Use the conversation history to maintain continuity — don't contradict
  yourself within a conversation
- Keep responses conversational, not lecture-like"""


def format_context_chunks(chunks: list[dict]) -> str:
    """
    Format retrieved context chunks for insertion into the prompt.

    Each chunk dict should have keys: 'doc_id', 'text' (or 'content'),
    and optionally 'score'.
    """
    if not chunks:
        return "[No relevant context found.]"

    lines = []
    for i, chunk in enumerate(chunks, 1):
        doc_id = chunk.get("doc_id", "Unknown Episode")
        text = chunk.get("text", chunk.get("content", ""))
        score = chunk.get("score")
        header = f"--- Context Chunk {i}: {doc_id}"
        if score is not None:
            header += f" (relevance: {score:.2f})"
            
        header += " ---"
        lines.append(header)
        lines.append(text.strip())
        lines.append("")

    return "\n".join(lines)


def format_story_prompt(query: str, context_chunks: list[dict], available_episodes: list[str]) -> list[dict]:
    """Assemble the full prompt for story summarisation mode."""
    context_text = format_context_chunks(context_chunks)
    episodes_text = ", ".join(available_episodes)
    
    system_prompt = f"""{STORY_SYSTEM_PROMPT}

AVAILABLE EPISODES (89 total): {episodes_text}"""

    user_prompt = f"""CONTEXT:
{context_text}

USER QUESTION:
{query}

Please provide a comprehensive, accurate answer based on the context above."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def format_doug_prompt(
    query: str,
    context_chunks: list[dict],
    conversation_history: list[dict] | None = None,
) -> list[dict]:
    """Assemble the full prompt for Doug Eiffel character mode."""
    context_text = format_context_chunks(context_chunks)
    history = conversation_history or []

    system_prompt = f"""{CHARACTER_SYSTEM_PROMPT}

CONTEXT (use this to inform your answers, but respond as Doug):
{context_text}"""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Append past conversation history
    for msg in history:
        messages.append(msg)
        
    # Append current user query
    messages.append({"role": "user", "content": query})
    
    return messages
