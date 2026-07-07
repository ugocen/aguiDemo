from agents.content_studio import ContentStudioAgent
from agents.growth_analyst import GrowthAnalystAgent
from agents.incident_commander import IncidentCommanderAgent
from agents.math_coach import MathCoachAgent
from agents.platform_architect import PlatformArchitectAgent
from agents.research_desk import ResearchDeskAgent
from agents.travel_concierge import TravelConciergeAgent
from agents.trip_architect import TripArchitectAgent

_AGENT_CLASSES = [
    ResearchDeskAgent,
    TripArchitectAgent,
    IncidentCommanderAgent,
    GrowthAnalystAgent,
    ContentStudioAgent,
    TravelConciergeAgent,
    PlatformArchitectAgent,
    MathCoachAgent,
]

SCENARIO_AGENTS = {cls.id: cls for cls in _AGENT_CLASSES}


def build_scenario_agent(agent_id: str, settings=None):
    """Build a scenario agent.

    In ``langgraph`` mode with a provider key, scenarios that declare a
    ``system_prompt`` are driven by the model (it decides which cards to render,
    limited to the scenario's ``allowed_tools``). Otherwise the deterministic
    scripted agent runs, so the demo and the smoke work without credentials.
    """
    cls = SCENARIO_AGENTS.get(agent_id)
    if cls is None:
        return None
    system_prompt = getattr(cls, "system_prompt", None)
    if settings is not None and settings.agent_mode == "langgraph" and system_prompt:
        from app.llm.factory import has_llm_credentials

        if has_llm_credentials(settings):
            from app.agent.llm_agent import LLMToolAgent

            return LLMToolAgent(
                settings,
                system_prompt=system_prompt,
                allowed_tools=getattr(cls, "allowed_tools", None),
            )
    return cls()


def scenario_descriptors() -> list[dict[str, str]]:
    return [
        {"id": cls.id, "name": cls.name, "description": cls.description} for cls in _AGENT_CLASSES
    ]
