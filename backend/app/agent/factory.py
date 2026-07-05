from app.agent.graph import LangGraphAgent
from app.agent.mock import MockAgent
from app.config.settings import Settings


def build_agent(settings: Settings):
    if settings.agent_mode == "langgraph":
        return LangGraphAgent(settings)
    return MockAgent()
