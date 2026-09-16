"""
Centralized application configuration.

Every module that needs a config value (DB URL, API key, model name, feature
flag) imports `settings` from here rather than calling os.environ directly.
This keeps configuration in one place and makes it trivial to see everything
the app depends on.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    environment: str = "development"
    app_secret_key: str = "dev-secret-change-me"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://salesops:salesops@localhost:5432/salesops"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Auth
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""

    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "openai"
    llm_model_fast: str = ""
    llm_model_reasoning: str = ""

    # Observability
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "salesops-ai"

    # Integrations
    hubspot_access_token: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached so we don't re-parse the environment on every import."""
    return Settings()


settings = get_settings()
