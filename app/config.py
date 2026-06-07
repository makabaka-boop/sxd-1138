from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "洗护门店管理系统"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8112
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./laundry.db"

    SECRET_KEY: str = "laundry-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    class Config:
        env_file = ".env"


settings = Settings()
