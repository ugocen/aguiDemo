# Phase 2, AgentCore packaging (prepared, deployed manually later)

The same agent that runs locally in `backend/app/agent/` is packaged here for
Amazon Bedrock AgentCore. The container reuses `app.agent.factory.build_agent`
and `app.agui.translator.Translator`, so the AG-UI event stream is identical
whether the agent runs locally or on AgentCore.

The runtime contract is a container that listens on port `8080` and exposes:

- `GET /ping`, health check.
- `POST /invocations`, body is `RunAgentInput`, response is the AG-UI event
  stream over `text/event-stream`.

## Build the image

Run from the repository root so both `backend/` and `deploy/` are in context:

```bash
docker build -f deploy/agentcore/Dockerfile -t agui-demo-agent:latest .
docker run --rm -p 8080:8080 --env-file .env agui-demo-agent:latest
curl -s localhost:8080/ping
```

## Path A, AgentCore CLI

```bash
pip install bedrock-agentcore-starter-toolkit
agentcore configure --entrypoint deploy/agentcore/agentcore_app.py --name agui-demo-agent
agentcore launch
```

## Path B, ECR then register

```bash
aws ecr create-repository --repository-name agui-demo-agent
docker tag agui-demo-agent:latest <acct>.dkr.ecr.<region>.amazonaws.com/agui-demo-agent:latest
aws ecr get-login-password | docker login --username AWS --password-stdin <acct>.dkr.ecr.<region>.amazonaws.com
docker push <acct>.dkr.ecr.<region>.amazonaws.com/agui-demo-agent:latest
```

Then register the image as an AgentCore Runtime agent (console or
`aws bedrock-agentcore-control create-agent-runtime`), pointing at the pushed
image and setting the environment variables from `.env`.

## After deploy

Point the frontend at the AgentCore endpoint by changing only `lib/agui.ts`
(the `BACKEND_URL` / endpoint target). The local FastAPI path stays available
for comparison.
