"""
Authentication utilities: password hashing, JWT tokens, dependency injection.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db
from app.models import User, UserRole
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise unauthorized

    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise unauthorized

    user_id = payload.get("sub")
    if not user_id:
        raise unauthorized

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise unauthorized
    return user


# ─── Role Permission Map ──────────────────────────────────────────────────────

ROLE_PERMISSIONS = {
    UserRole.super_admin: {
        "candidates:read", "candidates:write", "candidates:delete",
        "requisitions:read", "requisitions:write", "requisitions:delete",
        "scoring:read", "scoring:run",
        "sync:read", "sync:manage",
        "users:read", "users:write", "users:delete",
        "settings:read", "settings:write",
        "audit:read",
        "documents:read", "documents:write", "documents:delete",
        "analytics:read",
        "filters:read", "filters:write", "filters:delete",
        "prompts:read", "prompts:write",
    },
    UserRole.hr_admin: {
        "candidates:read", "candidates:write",
        "requisitions:read", "requisitions:write",
        "scoring:read", "scoring:run",
        "sync:read",
        "documents:read", "documents:write",
        "analytics:read",
        "filters:read", "filters:write",
    },
    UserRole.recruiter: {
        "candidates:read", "candidates:write",
        "scoring:read",
        "documents:read", "documents:write",
        "filters:read", "filters:write",
    },
    UserRole.technical_team: {
        "candidates:read",
        "scoring:read",
        "filters:read",
    },
    UserRole.requester: {
        "candidates:read",
        "filters:read",
    },
    UserRole.viewer: {
        "candidates:read",
        "filters:read",
    },
}


def has_permission(user: User, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(user.role, set())
    return permission in perms


def require_permission(permission: str):
    """Dependency factory that checks a specific permission."""
    async def _check(user: User = Depends(get_current_user)):
        if not has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user
    return _check
