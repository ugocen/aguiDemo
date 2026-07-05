from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.entra import Principal, get_current_principal
from app.config.settings import Settings, get_settings

router = APIRouter(tags=["agents"])


class AgentDescriptor(BaseModel):
    id: str
    name: str
    description: str


def _parse_agents(raw: str) -> list[AgentDescriptor]:
    agents: list[AgentDescriptor] = []
    for entry in raw.split(","):
        parts = entry.split(":")
        if len(parts) < 2:
            continue
        agent_id = parts[0].strip()
        name = parts[1].strip()
        description = parts[2].strip() if len(parts) > 2 else ""
        if agent_id and name:
            agents.append(AgentDescriptor(id=agent_id, name=name, description=description))
    return agents


@router.get("/agents", response_model=list[AgentDescriptor])
async def list_agents(
    _principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[AgentDescriptor]:
    return _parse_agents(settings.demo_agents)
