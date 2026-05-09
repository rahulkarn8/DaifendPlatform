# Build from repository root: docker build -f apps/memory-integrity-engine/Dockerfile .
FROM python:3.12-slim
WORKDIR /app
COPY packages/daifend-core /packages/daifend-core
COPY apps/memory-integrity-engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir "/packages/daifend-core[observability]" -r /app/requirements.txt
COPY apps/memory-integrity-engine/daifend_memory /app/daifend_memory
COPY apps/memory-integrity-engine/daifend_grpc /app/daifend_grpc
COPY apps/memory-integrity-engine/app /app/app
COPY apps/memory-integrity-engine/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
ENV PYTHONPATH=/app/daifend_grpc
ENV PYTHONUNBUFFERED=1
EXPOSE 8003 50051
CMD ["/app/docker-entrypoint.sh"]
