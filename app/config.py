from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    #  Configuration schema with type hints
    ENVIRONMENT: str
    APP_NAME: str
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" #  Ignores extra system variables from the terminal environment
    )

settings = Settings()
