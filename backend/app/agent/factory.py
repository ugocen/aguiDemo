import sys
from pathlib import Path

from app.agent.graph import LangGraphAgent
from app.agent.mock import MockAgent
from app.config.settings import Settings
from app.logging.setup import get_logger

log = get_logger("agent_factory")


def ensure_agents_on_path() -> bool:
    """Put the directory containing the top-level ``agents`` package on sys.path.

    Walks up from this file so the same code works from the source tree and from
    container layouts where the package sits next to ``app``.
    """
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "agents" / "registry.py").exists():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return True
    return False


def build_agent(settings: Settings, agent_id: str | None = None):
    """Select the agent for a run.

    A selected scenario agent (from the top-level ``agents`` package) wins when
    present, otherwise the run falls back to the configured mode, langgraph or
    the scripted mock.
    """
    if agent_id:
        ensure_agents_on_path()
        try:
            from agents.registry import build_scenario_agent

            scenario = build_scenario_agent(agent_id)
            if scenario is not None:
                return scenario
        except Exception as exc:  # noqa: BLE001
            log.warning("scenario_load_failed", agent_id=agent_id, error=str(exc))

    if settings.agent_mode == "langgraph":
        return LangGraphAgent(settings)
    return MockAgent()
