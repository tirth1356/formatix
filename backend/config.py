"""
FormatIX — Application Configuration
Uses pydantic-settings for typed env var loading with validation.

Environment variables (all optional — sensible defaults provided):
  AI_MODE                  local | cloud           (default: local)
  OLLAMA_BASE_URL          http://localhost:11434
  OLLAMA_MODEL_FAST        phi3
  OLLAMA_MODEL_REASONING   llama3
  GROQ_API_KEY             sk-...                  (required for cloud mode)
  GROQ_MODEL_FAST          llama-3.1-8b-instant    (fast tasks: parsing, rules)
  GROQ_MODEL_REASONING     llama-3.3-70b-versatile (heavy: corrections, validation)
  SERVER_HOST              0.0.0.0
  SERVER_PORT              8000
  UPLOAD_DIR               ./uploads
  OUTPUT_DIR               ./outputs
  MAX_FILE_SIZE_MB         20
  JOB_TTL_SECONDS          3600                    (in-memory job expiry)
  CORS_ORIGINS             *                       (comma-separated or "*")
  LOG_LEVEL                INFO

Copy .env.example → .env and fill in your values.
"""
import logging
from functools import lru_cache
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── AI mode ───────────────────────────────────────────────────────────────
    ai_mode: str = "local"          # "local" | "cloud"

    # ── Ollama (local) ────────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_fast: str = "phi3"
    ollama_model_reasoning: str = "llama3"

    # ── Groq (cloud) ─────────────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model_fast: str = "llama-3.1-8b-instant"
    groq_model_reasoning: str = "llama-3.1-8b-instant"
    # Legacy single-model field kept for backward compat — maps to reasoning
    groq_model: str = ""

    # ── Server ────────────────────────────────────────────────────────────────
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # ── Storage ───────────────────────────────────────────────────────────────
    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"
    max_file_size_mb: int = 20

    # ── Jobs ─────────────────────────────────────────────────────────────────
    job_ttl_seconds: int = 3600     # seconds before in-memory jobs are evicted

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: str = "*"         # comma-separated list or "*"

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ─────────────────────────────────────────────────────────────────────────
    # Validators
    # ─────────────────────────────────────────────────────────────────────────

    @field_validator("ai_mode")
    @classmethod
    def _validate_ai_mode(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("local", "cloud"):
            raise ValueError("AI_MODE must be 'local' or 'cloud'")
        return v

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        v = v.upper().strip()
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in valid:
            raise ValueError(f"LOG_LEVEL must be one of {valid}")
        return v

    @field_validator("server_port")
    @classmethod
    def _validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError("SERVER_PORT must be between 1 and 65535")
        return v

    @field_validator("max_file_size_mb")
    @classmethod
    def _validate_file_size(cls, v: int) -> int:
        if v < 1 or v > 500:
            raise ValueError("MAX_FILE_SIZE_MB must be between 1 and 500")
        return v

    @model_validator(mode="after")
    def _backfill_groq_model(self) -> "Settings":
        """
        Backward compat: if legacy groq_model is set, use it as the reasoning
        model when groq_model_reasoning is still at its default value.
        Always keep groq_model in sync with groq_model_reasoning so old code
        that reads settings.groq_model still works.
        """
        default_reasoning = "llama-3.1-8b-instant"
        if self.groq_model and self.groq_model_reasoning == default_reasoning:
            object.__setattr__(self, "groq_model_reasoning", self.groq_model)
        # Always keep legacy field in sync
        object.__setattr__(self, "groq_model", self.groq_model_reasoning)
        return self

    # ─────────────────────────────────────────────────────────────────────────
    # Computed properties (read-only helpers used throughout the app)
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def use_cloud(self) -> bool:
        """True only when cloud mode is active AND a Groq API key is present."""
        return self.ai_mode == "cloud" and bool(self.groq_api_key.strip())

    @property
    def active_model_fast(self) -> str:
        """Fast model for the active backend (parsing, rule extraction)."""
        return self.groq_model_fast if self.use_cloud else self.ollama_model_fast

    @property
    def active_model_reasoning(self) -> str:
        """Reasoning model for the active backend (corrections, validation)."""
        return self.groq_model_reasoning if self.use_cloud else self.ollama_model_reasoning

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS_ORIGINS string → list. '*' stays as ['*']."""
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def configure_logging(self) -> None:
        """Apply LOG_LEVEL to the root logger. Called once at startup."""
        logging.basicConfig(
            level=getattr(logging, self.log_level, logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def log_startup(self) -> None:
        """Emit a startup summary so operators can confirm active settings."""
        log = logging.getLogger(__name__)
        log.info("FormatIX starting — ai_mode=%s  use_cloud=%s", self.ai_mode, self.use_cloud)
        if self.use_cloud:
            log.info("  Groq fast=%s  reasoning=%s", self.groq_model_fast, self.groq_model_reasoning)
        else:
            log.info("  Ollama url=%s  fast=%s  reasoning=%s",
                     self.ollama_base_url, self.ollama_model_fast, self.ollama_model_reasoning)
            if not self.groq_api_key:
                log.warning("  GROQ_API_KEY not set — cloud mode unavailable")
        log.info("  upload_dir=%s  output_dir=%s  max_file_size=%sMB",
                 self.upload_dir, self.output_dir, self.max_file_size_mb)


@lru_cache()
def get_settings() -> Settings:
    """
    Cached singleton. Call this everywhere instead of constructing Settings().
    The cache is intentionally never invalidated in production; restart to reload.
    """
    s = Settings()
    s.configure_logging()
    return s