FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock* .

RUN uv sync --frozen

COPY app/ ./app
COPY scripts/ ./scripts 
COPY alembic.ini .

RUN chmod +x /app/scripts/entry.sh

EXPOSE 8000

CMD /bin/sh ./scripts/entry.sh