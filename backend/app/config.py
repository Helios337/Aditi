from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = "http://localhost:54321"
    supabase_service_role_key: str = "replace-me"
    supabase_jwt_secret: str = "replace-me"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    openrouter_vision_model: str = "qwen/qwen2.5-vl-72b-instruct:free"
    openrouter_text_model: str = "deepseek/deepseek-r1:free"
    openrouter_site_url: str = "https://github.com/Helios337/Aditi"
    openrouter_site_name: str = "Aditi"

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
