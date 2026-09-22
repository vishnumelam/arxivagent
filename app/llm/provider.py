import json
import requests
from app.config import (
    LLM_PROVIDER, GROQ_API_KEY, GROQ_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL
)

class LLMError(RuntimeError):
    pass

def _groq_chat(system: str, user: str) -> str:
    if not GROQ_API_KEY:
        raise LLMError("GROQ_API_KEY is not configured.")
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content

def _ollama_chat(system: str, user: str) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "options": {"temperature": 0.1},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]

def chat(system: str, user: str) -> str:
    provider = LLM_PROVIDER
    if provider == "groq":
        return _groq_chat(system, user)
    if provider == "ollama":
        return _ollama_chat(system, user)
    if provider:
        raise LLMError(f"Unsupported LLM_PROVIDER: {provider}")

    # Automatic fallback: Groq when configured, otherwise Ollama.
    if GROQ_API_KEY:
        return _groq_chat(system, user)
    return _ollama_chat(system, user)
