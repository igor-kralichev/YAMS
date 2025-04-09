import os

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Срок действия access-токена в минутах
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7 # Срок действия refresh-токена в днях
    DATABASE_URL: str  # Добавляем поле для DATABASE_URL
    APP_URL: str = "http://localhost:8000"  # Если используете для отправки email
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_file_encoding = "utf-8"

settings = Settings()