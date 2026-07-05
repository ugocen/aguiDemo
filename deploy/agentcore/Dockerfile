FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/pyproject.toml ./backend/pyproject.toml
RUN pip install --upgrade pip && pip install ./backend

COPY backend/app ./backend/app
COPY agents ./agents
COPY deploy/agentcore/agentcore_app.py ./agentcore_app.py

EXPOSE 8080

CMD ["uvicorn", "agentcore_app:app", "--host", "0.0.0.0", "--port", "8080"]
