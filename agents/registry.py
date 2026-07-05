from agents.data_analyst import DataAnalystAgent
from agents.doc_writer import DocWriterAgent
from agents.research_assistant import ResearchAssistantAgent
from agents.support_triage import SupportTriageAgent

_AGENT_CLASSES = [
    ResearchAssistantAgent,
    DocWriterAgent,
    DataAnalystAgent,
    SupportTriageAgent,
]

SCENARIO_AGENTS = {cls.id: cls for cls in _AGENT_CLASSES}


def build_scenario_agent(agent_id: str):
    cls = SCENARIO_AGENTS.get(agent_id)
    return cls() if cls is not None else None


def scenario_descriptors() -> list[dict[str, str]]:
    return [
        {"id": cls.id, "name": cls.name, "description": cls.description} for cls in _AGENT_CLASSES
    ]
