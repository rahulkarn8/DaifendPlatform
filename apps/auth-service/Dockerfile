# Build from repository root: docker build -f apps/auth-service/Dockerfile .
FROM python:3.12-slim
WORKDIR /app
COPY packages/daifend-core /packages/daifend-core
COPY apps/auth-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir "/packages/daifend-core" -r /app/requirements.txt
COPY apps/auth-service/app /app/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
