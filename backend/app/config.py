from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = "http://localhost:54321"
    supabase_service_role_key: str = "replace-me"
    supabase_jwt_secret: str = "replace-me"

    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    nvidia_model: str = "minimaxai/minimax-m3"

    cors_origins: str = "http://localhost:3000"
    admin_emails: str = ""
    storage_bucket: str = "question-images"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def admin_email_list(self) -> list[str]:
        return [email.strip().lower() for email in self.admin_emails.split(",") if email.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
