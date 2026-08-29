import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


# Create engine - works with both SQLite and PostgreSQL
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {}
if is_sqlite:
    connect_args["check_same_thread"] = False
elif "postgresql" in settings.DATABASE_URL:
    # Use a normal, fully-verified TLS connection (Neon and most managed
    # Postgres providers use publicly-trusted certs — no need to disable
    # verification, which would allow a man-in-the-middle).
    connect_args["ssl"] = True

# Serverless (Vercel) functions are short-lived, stateless processes — a
# large persistent pool per invocation just exhausts Postgres connections.
# Use a small pool in that environment; a normal pool otherwise.
is_serverless = bool(os.environ.get("VERCEL"))

engine_kwargs = dict(
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args=connect_args,
)
if not is_sqlite:
    # SQLite's async driver uses NullPool and doesn't accept pool sizing
    # kwargs — only pass these for real (pooled) databases like Postgres.
    engine_kwargs.update(
        pool_size=1 if is_serverless else 5,
        max_overflow=0 if is_serverless else 10,
        pool_recycle=300,
        pool_timeout=30,
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
