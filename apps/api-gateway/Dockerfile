# Build from repository root: docker build -f apps/api-gateway/Dockerfile .
FROM python:3.12-slim
WORKDIR /app
COPY packages/daifend-core /packages/daifend-core
COPY apps/memory-integrity-engine/daifend_grpc /app/daifend_grpc
COPY apps/api-gateway/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir "/packages/daifend-core[observability]" -r /app/requirements.txt
COPY apps/api-gateway/app /app/app
ENV PYTHONPATH=/app/daifend_grpc
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
