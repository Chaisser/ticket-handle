from dataclasses import dataclass
from os import getenv

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


@dataclass(frozen=True)
class Settings:
    model: str
    confidence_threshold: float


def get_settings() -> Settings:
    return Settings(
        model=getenv("LLM_MODEL", "openai:gpt-4o-mini"),
        confidence_threshold=float(getenv("CONFIDENCE_THRESHOLD", "0.7")),
    )


def build_llm(settings: Settings) -> BaseChatModel:
    return init_chat_model(settings.model, temperature=0)
