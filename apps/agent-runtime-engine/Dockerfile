# Build from repository root: docker build -f apps/agent-runtime-engine/Dockerfile .
FROM python:3.12-slim
WORKDIR /app
COPY packages/daifend-core /packages/daifend-core
COPY apps/agent-runtime-engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir /packages/daifend-core -r /app/requirements.txt
COPY apps/agent-runtime-engine/app /app/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
