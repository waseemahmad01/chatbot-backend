from openai import OpenAI
from app.core.config import settings
from ollama import Client

PROVIDERS = {
    "groq": OpenAI(base_url="https://api.groq.com/openai/v1", api_key=settings.groq_api_key),
    "ollama": Client(base_url="http://localhost:11434"),
}

MODELS = {
    "llama-3.1-8b-instant": "groq",
    "openai/gpt-oss-20b": "groq",
    "openai/gpt-oss-120b": "groq",
    "qwen":"ollama"
}

def get_client(model: str) -> OpenAI:
    provider = MODELS[model]
    return PROVIDERS[provider]