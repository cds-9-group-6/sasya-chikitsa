import os

try:
    from langchain_openai import ChatOpenAI  # type: ignore
except Exception:  # pragma: no cover
    ChatOpenAI = None  # type: ignore

try:
    from langchain_ollama import ChatOllama  # type: ignore
except Exception:  # pragma: no cover
    try:
        from langchain_community.chat_models import ChatOllama  # type: ignore
    except Exception:  # pragma: no cover
        ChatOllama = None  # type: ignore


def create_llm():
    """Create a chat model. Prefers OpenAI if OPENAI_API_KEY is set, otherwise tries Ollama."""
    ollama_host = os.getenv("OLLAMA_HOST")
    api_key = os.getenv("OPENAI_API_KEY")
    if ChatOpenAI is not None and api_key:
        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2)
    if ChatOllama is not None and (ollama_host or os.path.exists("/usr/local/bin/ollama")):
        if ollama_host:
            return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"), temperature=0.2, base_url=ollama_host)
        return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"), temperature=0.2)
    raise RuntimeError(
        "No chat model configured. Set OPENAI_API_KEY (and optionally OPENAI_MODEL) or run Ollama and set OLLAMA_MODEL."
    )


