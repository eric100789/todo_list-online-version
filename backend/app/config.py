from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # App
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ENABLE_REGISTRATION: bool = Field(True, env="ENABLE_REGISTRATION")
    DEBUG: bool = Field(False, env="DEBUG")

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
