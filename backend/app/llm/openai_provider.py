from app.config.settings import Settings
from app.llm.openai_compatible import OpenAICompatibleClient


class OpenAIClient(OpenAICompatibleClient):
    """OpenAI (or any OpenAI-compatible vendor) via the chat completions API."""

    provider = "openai"

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            stream_mode=settings.llm_stream_mode,
            timeout_seconds=settings.llm_timeout_seconds,
        )
