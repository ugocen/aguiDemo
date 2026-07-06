from app.config.settings import Settings
from app.llm.anthropic_provider import AnthropicClient
from app.llm.base import LLMClient
from app.llm.gemini_provider import GeminiClient
from app.llm.marketplace import MarketplaceClient
from app.llm.openai_provider import OpenAIClient


def build_llm(settings: Settings) -> LLMClient:
    """The single model path. Selects the vendor client from LLM_PROVIDER.

    All clients expose the same `stream_completion(messages)` interface, so the
    agent works unchanged with the Marketplace gateway, OpenAI, Anthropic
    (Claude), or Google (Gemini).
    """
    provider = settings.llm_provider
    if provider == "openai":
        return OpenAIClient(settings)
    if provider == "anthropic":
        return AnthropicClient(settings)
    if provider == "gemini":
        return GeminiClient(settings)
    return MarketplaceClient(settings)


def has_llm_credentials(settings: Settings) -> bool:
    """True when the selected provider has an API key configured.

    Lets callers fall back to scripted behavior when ``langgraph`` mode is set
    without a usable key (so the demo and the smoke stay deterministic).
    """
    return bool(
        {
            "openai": settings.openai_api_key,
            "anthropic": settings.anthropic_api_key,
            "gemini": settings.gemini_api_key,
            "marketplace": settings.marketplace_api_key,
        }.get(settings.llm_provider)
    )
