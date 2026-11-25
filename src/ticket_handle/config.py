from dataclasses import dataclass
from os import getenv

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


@dataclass(frozen=True)
class Settings:
    model: str
    confidence_threshold: float
    temperature: float | None


def get_settings() -> Settings:
    raw_temperature = getenv("LLM_TEMPERATURE", "0")
    return Settings(
        model=getenv("LLM_MODEL", "openai:gpt-4o-mini"),
        confidence_threshold=float(getenv("CONFIDENCE_THRESHOLD", "0.7")),
        temperature=float(raw_temperature) if raw_temperature else None,
    )


def build_llm(settings: Settings) -> BaseChatModel:
    kwargs = {}
    if settings.temperature is not None:
        kwargs["temperature"] = settings.temperature
    return init_chat_model(settings.model, **kwargs)
