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
