from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Final


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

DEFAULT_FRACTAL_CX: Final[float] = -0.7
DEFAULT_FRACTAL_CY: Final[float] = 0.27015
DEFAULT_FRACTAL_ZOOM: Final[float] = 1.0
DEFAULT_FRACTAL_ITERATIONS: Final[int] = 100