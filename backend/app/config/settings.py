from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    log_level: str = "info"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    cors_allow_origins: str = "http://localhost:3000"

    agent_mode: Literal["mock", "langgraph"] = "mock"

    # Vendor-agnostic model path. Pick the provider; all expose the same
    # streaming interface so the agent is unchanged across vendors.
    llm_provider: Literal["marketplace", "openai", "anthropic", "gemini"] = "marketplace"
    llm_stream_mode: Literal["stream", "chunked"] = "stream"
    llm_timeout_seconds: float = 60.0

    # Marketplace gateway (OpenAI-compatible)
    marketplace_base_url: str = "https://marketplace.example.com/v1"
    marketplace_api_key: str = ""
    marketplace_model: str = ""
    marketplace_tenant: str = ""
    marketplace_stream_mode: Literal["stream", "chunked"] = "stream"
    marketplace_timeout_seconds: float = 60.0

    # OpenAI (or any OpenAI-compatible vendor)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Anthropic (Claude)
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"
    anthropic_version: str = "2023-06-01"
    anthropic_max_tokens: int = 1024

    # Google Gemini
    gemini_base_url: str = "https://generativelanguage.googleapis.com"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    database_url: str = "postgresql+asyncpg://agui:agui@localhost:5432/agui"

    auth_mode: Literal["dev", "entra"] = "dev"
    dev_user_id: str = "dev-user"
    dev_user_email: str = "dev@example.com"

    entra_tenant_id: str = ""
    entra_client_id: str = ""
    entra_audience: str = ""
    entra_issuer: str = ""

    demo_agents: str = Field(
        default="local-langgraph:Local LangGraph Agent:The Phase 1 agent running on this machine,"
        "agentcore-researcher:Researcher (AgentCore):Deploys to Bedrock AgentCore in Phase 2,"
        "agentcore-writer:Writer (AgentCore):Deploys to Bedrock AgentCore in Phase 2",
        description="Comma separated agent descriptors, id:name:description",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
