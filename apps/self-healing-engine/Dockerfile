# Build from repository root: docker build -f apps/self-healing-engine/Dockerfile .
FROM python:3.12-slim
WORKDIR /app
COPY packages/daifend-core /packages/daifend-core
COPY apps/self-healing-engine/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir /packages/daifend-core -r /app/requirements.txt
COPY apps/self-healing-engine/app /app/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8005
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
