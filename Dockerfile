FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements-v2.txt .
RUN pip install --upgrade pip && pip install -r requirements-v2.txt

COPY backend ./backend
COPY ui ./ui
COPY skills ./skills
COPY AGENT_OS_V2.md README.md ./

EXPOSE 8000 8501

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
