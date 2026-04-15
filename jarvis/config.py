"""Configuration management for JARVIS."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """JARVIS configuration settings."""

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL: str = os.getenv("JARVIS_MODEL", "gpt-4o")

    # Memory settings
    MEMORY_DB: str = os.getenv(
        "JARVIS_MEMORY_DB",
        str(Path.home() / ".jarvis" / "memory.db"),
    )
    MAX_HISTORY: int = int(os.getenv("JARVIS_MAX_HISTORY", "20"))
    MAX_MEMORIES: int = int(os.getenv("JARVIS_MAX_MEMORIES", "5"))

    # User settings
    USER_NAME: str = os.getenv("JARVIS_USER_NAME", "")
    LANGUAGE: str = os.getenv("JARVIS_LANGUAGE", "auto")

    # Tool settings
    ENABLE_WEB_SEARCH: bool = os.getenv("JARVIS_ENABLE_WEB_SEARCH", "true").lower() == "true"
    ENABLE_CODE_EXEC: bool = os.getenv("JARVIS_ENABLE_CODE_EXEC", "true").lower() == "true"
    ENABLE_FILE_OPS: bool = os.getenv("JARVIS_ENABLE_FILE_OPS", "true").lower() == "true"

    # JARVIS personality
    JARVIS_NAME: str = "JARVIS"

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration. Returns list of errors."""
        errors = []
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set. Please set it in your .env file.")
        return errors

    @classmethod
    def ensure_memory_dir(cls) -> None:
        """Ensure the memory directory exists."""
        Path(cls.MEMORY_DB).parent.mkdir(parents=True, exist_ok=True)


config = Config()
