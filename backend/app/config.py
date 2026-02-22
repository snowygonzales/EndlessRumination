from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env from backend/ directory before pydantic-settings reads env vars
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_FILE, override=True)


class Settings(BaseSettings):
    app_name: str = "Endless Rumination API"
    debug: bool = False

    # Claude API
    anthropic_api_key: str = ""
    claude_model_sonnet: str = "claude-sonnet-4-20250514"
    claude_model_haiku: str = "claude-haiku-4-5-20251001"
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
    free_takes_per_day: int = 5       # 5 lenses per submission for free
    free_problems_per_day: int = 1    # 1 submission per day for free
    free_problems_per_month: int = 3  # 3 submissions per month for free
    pro_problems_per_day: int = 50    # effectively unlimited for pro

    # Free tier lens config: indices of lenses that use Sonnet ("Wise")
    # The Stoic (1) and The Therapist (9) — best quality for free taste
    free_sonnet_lens_indices: list[int] = [1, 9]
    free_lens_count: int = 5          # total lenses shown to free users

    # Batch generation
    parallel_batch_size: int = 5  # Claude calls to fire at once


@lru_cache
def get_settings() -> Settings:
    return Settings()
