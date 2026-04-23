from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str             = ""
    llm_model: str                = ""
    groq_api_key: str             = ""
    openai_api_key: str           = ""
    request_timeout_seconds: int  = 45
    max_chars_per_chunk: int      = 6000
    output_dir: Path              = Path("sample_outputs")
    log_level: str                = "INFO"

    def __post_init__(self) -> None:
        # Read from env at instantiation time so that importlib.reload()
        # and os.environ overrides are picked up correctly.
        object.__setattr__(self, "llm_provider",
            os.getenv("LLM_PROVIDER", "groq").strip().lower())
        object.__setattr__(self, "llm_model",
            os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip())
        object.__setattr__(self, "groq_api_key",
            os.getenv("GROQ_API_KEY", "").strip())
        object.__setattr__(self, "openai_api_key",
            os.getenv("OPENAI_API_KEY", "").strip())
        object.__setattr__(self, "request_timeout_seconds",
            int(os.getenv("REQUEST_TIMEOUT_SECONDS", "45")))
        object.__setattr__(self, "max_chars_per_chunk",
            int(os.getenv("MAX_CHARS_PER_CHUNK", "6000")))
        object.__setattr__(self, "output_dir",
            Path(os.getenv("OUTPUT_DIR", "sample_outputs")))
        object.__setattr__(self, "log_level",
            os.getenv("LOG_LEVEL", "INFO").strip().upper())

    def validate(self) -> None:
        if self.llm_provider not in {"groq", "openai"}:
            raise ValueError("LLM_PROVIDER must be 'groq' or 'openai'.")
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq.")
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")


settings = Settings()
