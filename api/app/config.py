from pydantic_settings import BaseSettings
from typing import Optional
import os
import secrets
import warnings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Vercel's Python runtime only allows writes under /tmp — everything else
# (including this project directory) is read-only at runtime.
IS_VERCEL = bool(os.environ.get("VERCEL"))
DEFAULT_SQLITE_PATH = "/tmp/talent_pool.db" if IS_VERCEL else os.path.join(BASE_DIR, "talent_pool.db")
# NOTE: /tmp on Vercel is ephemeral and local to a single function
# invocation/instance — files written here are NOT guaranteed to persist
# or be visible across requests. This is fine for local dev, but for
# production CV storage on Vercel, point UPLOAD_DIR at (or replace this
# with) real object storage such as Vercel Blob or S3.
UPLOAD_DIR = os.environ.get(
    "UPLOAD_DIR",
    "/tmp/uploads/cvs" if IS_VERCEL else os.path.join(BASE_DIR, "uploads", "cvs"),
)
os.makedirs(UPLOAD_DIR, exist_ok=True)


def clean_database_url(url: str) -> str:
    """Remove unsupported query params from the URL for asyncpg."""
    if "?" in url:
        base, query = url.split("?", 1)
        # Only keep params asyncpg understands
        safe = []
        for p in query.split("&"):
            key = p.split("=")[0]
            if key in ("ssl",):
                safe.append(p)
        return base if not safe else base + "?" + "&".join(safe)
    return url


class Settings(BaseSettings):
    APP_NAME: str = "Talent Pool Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # No hardcoded credentials. Falls back to a local SQLite file for
    # zero-config local development only — set DATABASE_URL for anything real.
    DATABASE_URL: str = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}")

    JWT_SECRET: str = os.environ.get("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # One-time admin bootstrap (see /api/admin/seed) — no defaults on purpose.
    SEED_ADMIN_EMAIL: Optional[str] = None
    SEED_ADMIN_PASSWORD: Optional[str] = None
    SEED_SECRET: Optional[str] = None

    ERP_NEXT_URL: Optional[str] = None
    ERP_API_KEY: Optional[str] = None
    ERP_API_SECRET: Optional[str] = None

    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_PRIMARY_MODEL: Optional[str] = None
    OPENROUTER_FALLBACK_MODEL: Optional[str] = None
    OPENROUTER_MAX_TOKENS: int = 4096
    OPENROUTER_TEMPERATURE: float = 0.3

    DEFAULT_SYNC_THRESHOLD: float = 60.0
    # Comma-separated list of allowed frontend origins, e.g.
    # "https://myapp.vercel.app,http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    @property
    def cors_origins_list(self) -> list:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
# Clean URL so asyncpg does not get sslmode/channel_binding params
settings.DATABASE_URL = clean_database_url(settings.DATABASE_URL)

# JWT_SECRET must be set explicitly — never ship a guessable default that
# would let anyone forge valid login tokens.
if not settings.JWT_SECRET:
    if os.environ.get("VERCEL") or os.environ.get("ENVIRONMENT") == "production":
        raise RuntimeError(
            "JWT_SECRET environment variable is not set. Generate one with "
            "`openssl rand -hex 32` and set it in your deployment environment."
        )
    warnings.warn(
        "JWT_SECRET is not set — using a random secret for this local process only. "
        "Tokens will not survive a restart. Set JWT_SECRET in .env for persistent sessions."
    )
    settings.JWT_SECRET = secrets.token_hex(32)
