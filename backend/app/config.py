from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Endless Rumination API"
    debug: bool = False

    # Claude API
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 400

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/endless_rumination"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 30  # 30 days

    # Rate limits
    free_takes_per_day: int = 10
    free_problems_per_day: int = 3
    pro_problems_per_day: int = 10

    # Batch generation
    parallel_batch_size: int = 5  # Claude calls to fire at once

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
