FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./

RUN uv sync --no-dev --no-cache

COPY agent ./agent

CMD ["uv", "run", "python", "-m", "agent.main"]
