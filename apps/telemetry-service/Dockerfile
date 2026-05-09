# Build from repository root: docker build -f apps/telemetry-service/Dockerfile .
FROM python:3.12-slim
WORKDIR /app
COPY packages/daifend-core /packages/daifend-core
COPY apps/telemetry-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir "/packages/daifend-core[observability]" -r /app/requirements.txt
COPY apps/telemetry-service/app /app/app
ENV PYTHONUNBUFFERED=1
EXPOSE 4001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4001"]
