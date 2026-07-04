from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-lite"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen-qwq-32b"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    RESEND_API_KEY: str = ""
    ADMIN_USERNAME: str = ""
    MAX_USERS: int = 50

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
