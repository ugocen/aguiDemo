import sys
from pathlib import Path

from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.agent.factory import build_agent  # noqa: E402
from app.agui.translator import Translator  # noqa: E402
from app.config.settings import get_settings  # noqa: E402

settings = get_settings()
app = FastAPI(title="AG-UI Demo Agent, AgentCore Runtime")


@app.get("/ping")
async def ping() -> dict:
    return {"status": "healthy"}


@app.post("/invocations")
async def invocations(input: RunAgentInput) -> StreamingResponse:
    """AgentCore runtime entrypoint.

    Reuses the same agent and translator as the local FastAPI backend so the
    identical AG-UI event stream is produced whether the agent runs locally or
    on Bedrock AgentCore. Identity handling and history persistence stay in the
    fronting app; this container hosts only the agent and its event stream.
    """
    encoder = EventEncoder()
    agent = build_agent(settings)
    translator = Translator(input=input, agent=agent, user_id="agentcore")

    async def body():
        async for event in translator.stream():
            yield encoder.encode(event)

    return StreamingResponse(body(), media_type="text/event-stream")
