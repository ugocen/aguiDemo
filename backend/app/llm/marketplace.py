from app.config.settings import Settings
from app.llm.base import LLMError
from app.llm.openai_compatible import OpenAICompatibleClient

MarketplaceError = LLMError


class MarketplaceClient(OpenAICompatibleClient):
    """GenAI Marketplace gateway, treated as an OpenAI-compatible endpoint."""

    provider = "marketplace"

    def __init__(self, settings: Settings) -> None:
        extra = {"X-Tenant": settings.marketplace_tenant} if settings.marketplace_tenant else None
        super().__init__(
            base_url=settings.marketplace_base_url,
            api_key=settings.marketplace_api_key,
            model=settings.marketplace_model,
            stream_mode=settings.marketplace_stream_mode,
            timeout_seconds=settings.marketplace_timeout_seconds,
            extra_headers=extra,
        )
