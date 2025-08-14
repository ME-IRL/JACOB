from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    OPENAI_API_BASE: str = Field("https://api.openai.com/v1", env="OPENAI_API_BASE")

    # Signal Configuration
    SIGNAL_SERVICE: Optional[str] = Field(None, env="SIGNAL_SERVICE")
    PHONE_NUMBER: Optional[str] = Field(None, env="PHONE_NUMBER")

    # Application Configuration
    SYSTEM_PROMPT: str = Field(
        'You are a Signal chat bot named J.A.C.O.B. , short for "Just Another Cool Online Bot". Use only as many words needed, but fewer than 800 words.',
        env="SYSTEM_PROMPT",
    )

    MESH_ADDITIONAL_PROMPT: str = Field(
        "Keep your messages short and concise. Do not use more than 200 characters and avoid any complex formatting or instructions. Do not respond in any way other than text and emojis.",
        env="MESH_ADDITIONAL_PROMPT",
    )

    MESH_SERIAL_PORT: str = Field("/dev/ttyACM0", env="MESH_SERIAL_PORT")

    # Database Configuration
    DATABASE_URL: str = Field("sqlite:///signal.db", env="DATABASE_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        if not cls().SIGNAL_SERVICE:
            raise ValueError("SIGNAL_SERVICE environment variable is required")
        if not cls().PHONE_NUMBER:
            raise ValueError("PHONE_NUMBER environment variable is required")
        if not cls().OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")


settings = Settings()


def get_settings() -> Settings:
    """Get validated application settings."""
    settings.validate()
    return settings
