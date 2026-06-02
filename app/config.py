from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    serpapi_key: str = ""
    anthropic_api_key: str = ""
    sendgrid_api_key: str = ""
    email_to: str = ""
    email_from: str = ""
    run_token: str = "dev-token"
    database_path: str = "/data/jobs.db"
    resume_path: str = "/data/resume.md"
    min_score: int = 60


settings = Settings()
