from groq import Groq
from config import GROQ_API_KEY, STORY_MODEL, CHARACTER_MODEL


# =========================
# Client
# =========================

def get_client() -> Groq:
    """Create and return a Groq client."""
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    return Groq(api_key=GROQ_API_KEY)


# =========================
# Model Configuration
# =========================

MODEL_CONFIGS = {
    "story": {
        "model": STORY_MODEL,
        "temperature": 0.3,
        "max_tokens": 1000,
        "top_p": 0.9,
        "frequency_penalty": 0.3,
        "presence_penalty": 0.0,
    },
    "character": {
        "model": CHARACTER_MODEL,
        "temperature": 0.7,
        "max_tokens": 1500,
        "top_p": 0.95,
        "frequency_penalty": 0.5,
        "presence_penalty": 0.3,
    },
}


def get_generation_config(mode: str) -> dict:
    """
    Return generation settings for a given mode.
    """
    if mode not in MODEL_CONFIGS:
        raise ValueError(
            f"Invalid mode '{mode}'. "
            f"Expected one of: {list(MODEL_CONFIGS.keys())}"
        )

    return MODEL_CONFIGS[mode]


# =========================
# Non-streaming Generation
# =========================

def generate(messages: list[dict], mode: str = "story") -> str:
    

    client = get_client()
    config = get_generation_config(mode)

    response = client.chat.completions.create(
        model=config["model"],
        messages=messages,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        top_p=config["top_p"],
        frequency_penalty=config["frequency_penalty"],
        presence_penalty=config["presence_penalty"],
        stream=False,
    )

    return response.choices[0].message.content.strip()


# =========================
# Streaming Generation
# =========================

def stream_generate(messages: list[dict], mode: str = "story"):
    
    client = get_client()
    config = get_generation_config(mode)

    stream = client.chat.completions.create(
        model=config["model"],
        messages=messages,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        top_p=config["top_p"],
        frequency_penalty=config["frequency_penalty"],
        presence_penalty=config["presence_penalty"],
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta

        if delta and delta.content:
            yield delta.content
