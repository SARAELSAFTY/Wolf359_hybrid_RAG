from groq import Groq
from config import GROQ_API_KEY, STORY_MODEL, CHARACTER_MODEL


def _get_client():
    """Return a configured Groq client."""
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your .env file."
        )
    return Groq(api_key=GROQ_API_KEY)


def generate(messages: list[dict], mode: str = "story") -> str:
    """
    Send messages to the Groq API and return the full response text.

    Args:
        messages: The assembled prompt messages list.
        mode: "story" or "character" — selects model and parameters.
    """
    client = _get_client()

    if mode == "character":
        model = CHARACTER_MODEL
        temperature = 0.7
        max_tokens = 1500
        top_p = 0.95
        frequency_penalty = 0.5
        presence_penalty = 0.3
    else:
        model = STORY_MODEL
        temperature = 0.3
        max_tokens = 1000
        top_p = 0.9
        frequency_penalty = 0.3
        presence_penalty = 0.0

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stream=False,
    )
    return response.choices[0].message.content


def stream_generate(messages: list[dict], mode: str = "story"):
    """
    Send messages to the Groq API and yield response tokens as they arrive.

    Yields:
        str: Individual content chunks from the streaming response.
    """
    client = _get_client()

    if mode == "character":
        model = CHARACTER_MODEL
        temperature = 0.7
        max_tokens = 1500
        top_p = 0.95
        frequency_penalty = 0.5
        presence_penalty = 0.3
    else:
        model = STORY_MODEL
        temperature = 0.3
        max_tokens = 1000
        top_p = 0.9
        frequency_penalty = 0.3
        presence_penalty = 0.0

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
