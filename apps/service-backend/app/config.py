# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "GlobalConnector"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "GlobalConnector"

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ALLOWED_HOSTS: List[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env")

    SOLANA_DESTINATION_ADDRESS: str
    MANDEL_COIN_MINT_ADDRESS: str

    @field_validator("DATABASE_URL", "SECRET_KEY")
    @classmethod
    def must_not_be_empty(cls, v, info):
        if not v or not v.strip():
            raise ValueError(f"{info.field_name.upper()} must not be empty")
        return v


settings = Settings()
