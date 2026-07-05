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

    marketplace_base_url: str = "https://marketplace.example.com/v1"
    marketplace_api_key: str = ""
    marketplace_model: str = ""
    marketplace_tenant: str = ""
    marketplace_stream_mode: Literal["stream", "chunked"] = "stream"
    marketplace_timeout_seconds: float = 60.0

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
