from pydantic import ConfigDict, EmailStr
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DB_URL: str
    REDIS_URL: str = "redis://redis:6379"
    REDIS_TTL: int = 3600
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 3600
    JWT_REFRESH_EXPIRATION_SECONDS: int = 60 * 24 * 7

    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.meta.ua"
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLD_NAME: str
    CLD_API_KEY: str
    CLD_API_SECRET: str

    model_config = ConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()