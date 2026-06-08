# Build from repo root: docker build -f agents/Dockerfile .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY agents/requirements.txt agents/requirements.txt
RUN pip install --no-cache-dir -r agents/requirements.txt

COPY agents/ agents/

WORKDIR /app/agents

EXPOSE 8000

# Render sets PORT; local default 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
