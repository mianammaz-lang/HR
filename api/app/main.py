"""
Talent Pool Management System - FastAPI Application
"""
import secrets
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — restricted to the configured frontend origin(s), not "*".
# ("*" combined with allow_credentials=True is both rejected by browsers
# and, if it weren't, would let any site read authenticated responses.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from app.routers import auth as auth_router
from app.routers import candidates as candidates_router
from app.routers import requisitions as req_router
from app.routers import scoring as scoring_router
from app.routers import filters as filters_router
from app.routers import settings as settings_router
from app.routers import analytics as analytics_router
from app.routers import documents as documents_router
from app.routers import search as search_router
from app.routers import webhook as webhook_router
from app.routers import forms as forms_router

app.include_router(auth_router.router)
app.include_router(candidates_router.router)
app.include_router(req_router.router)
app.include_router(scoring_router.router)
app.include_router(filters_router.router)
app.include_router(settings_router.router)
app.include_router(analytics_router.router)
app.include_router(documents_router.router)
app.include_router(search_router.router)
app.include_router(webhook_router.router)
app.include_router(forms_router.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION, "app": settings.APP_NAME}


@app.post("/api/admin/seed")
async def seed_admin(x_seed_secret: str = Header(default="")):
    """
    One-time bootstrap endpoint — creates the first super-admin user.

    Protected by SEED_SECRET so it can't be called by a stranger who finds
    the URL. Requires SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD and SEED_SECRET
    to be set in the environment; none of these ship with a default.
    Call it once after deploy, then consider unsetting SEED_SECRET.
    """
    from app.database import AsyncSessionLocal, init_db
    from app.models import User, UserRole
    from app.auth import hash_password
    from sqlalchemy import select

    if not (settings.SEED_SECRET and settings.SEED_ADMIN_EMAIL and settings.SEED_ADMIN_PASSWORD):
        raise HTTPException(
            status_code=503,
            detail="Seeding is not configured. Set SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD "
                   "and SEED_SECRET in your environment first.",
        )
    if not secrets.compare_digest(x_seed_secret, settings.SEED_SECRET):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Seed-Secret header")

    await init_db()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == settings.SEED_ADMIN_EMAIL))
        if not result.scalar_one_or_none():
            db.add(User(
                email=settings.SEED_ADMIN_EMAIL,
                full_name="Admin",
                hashed_password=hash_password(settings.SEED_ADMIN_PASSWORD),
                role=UserRole.super_admin,
                team="Administration",
            ))
            await db.commit()
            return {"status": "seeded", "users": 1}
        return {"status": "already_seeded"}
