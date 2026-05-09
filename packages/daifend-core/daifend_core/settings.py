from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    daifend_env: str = "development"
    postgres_url: str = (
        "postgresql+asyncpg://daifend:daifend@localhost:5432/daifend"
    )
    redis_url: str = "redis://localhost:6379/0"
    nats_url: str = "nats://localhost:4222"
    jwt_secret: str = "dev-secret-change-in-production"
    internal_service_token: str = "dev-internal-token"
    qdrant_url: str = "http://localhost:6333"
    clickhouse_url: str = "http://localhost:8123"
