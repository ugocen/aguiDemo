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


def _scenario_agents() -> list[AgentDescriptor]:
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    try:
        from agents.registry import scenario_descriptors

        return [AgentDescriptor(**d) for d in scenario_descriptors()]
    except Exception:
        return []


@router.get("/agents", response_model=list[AgentDescriptor])
async def list_agents(
    _principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> list[AgentDescriptor]:
    scenarios = _scenario_agents()
    if scenarios:
        return scenarios
    return _parse_agents(settings.demo_agents)
