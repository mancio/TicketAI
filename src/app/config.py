"""Configuration loading and validation."""

import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Environment-driven configuration (fail-fast validation)."""

    environment: str = Field("development", description="Environment name")
    log_level: str = Field("INFO", description="Logging level")
    max_input_length: int = Field(5000, description="Max input length in chars")

    def validate_or_raise(self) -> None:
        if self.environment not in {"development", "staging", "production"}:
            raise ValueError("ENVIRONMENT must be development, staging, or production")
        if self.max_input_length < 100:
            raise ValueError("MAX_INPUT_LENGTH must be >= 100")


def get_settings() -> Settings:
    settings = Settings(
        environment=os.getenv("ENVIRONMENT", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        max_input_length=int(os.getenv("MAX_INPUT_LENGTH", "5000")),
    )
    settings.validate_or_raise()
    return settings
