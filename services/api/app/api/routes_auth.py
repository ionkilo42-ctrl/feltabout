"""
Authentication routes for Feltabout.

Endpoints:
- POST /auth/magic-link-request - Request a magic link email
- GET /auth/verify - Verify magic link token and get session
- POST /auth/update-name - Update user's display name
- GET /auth/me - Get current user info
"""

import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.services.auth_service import (
    AuthService,
    create_session_token,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── Request/Response Models ──────────────────────────────────────────────────

class MagicLinkRequest(BaseModel):
    email: EmailStr
    next: Optional[str] = None  # Post-login redirect path


class VerifyResponse(BaseModel):
    token: str
    user_id: str
    email: str
    name: str


class UpdateNameRequest(BaseModel):
    name: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str


class MagicLinkResponse(BaseModel):
    message: str
    # For dev: include the link in response (logged to console in production)


# ─── Auth Dependencies ────────────────────────────────────────────────────────

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_current_user(
    authorization: str = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get current user from Authorization header.
    Returns user payload or None if not authenticated.
    """
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split("Bearer ")[1]
    payload = decode_token(token)
    
    if not payload:
        return None
    
    return payload


async def require_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require authenticated user, raise 401 if not (dev mode returns dev user when auth disabled)."""
    USE_AUTH = os.environ.get("USE_AUTH", "false") == "true"
    
    if USE_AUTH and not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Dev mode: return dev user when auth is disabled
    if not current_user:
        return {"sub": "dev-user-001", "email": "dev@feltabout.local", "name": "Dev User"}
    
    return current_user


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/magic-link-request", response_model=MagicLinkResponse)
async def request_magic_link(
    data: MagicLinkRequest,
    auth: AuthService = Depends(get_auth_service),
):
    """
    Request a magic link to sign in.

    For MVP, the link is logged to console. In production, this would
    send an actual email via Resend/SendGrid/etc.
    """
    raw_token, invite_url = await auth.request_magic_link(data.email, data.next)

    return MagicLinkResponse(
        message="Magic link sent! Check your email (or see server console for dev link)",
    )


@router.get("/verify", response_model=VerifyResponse)
async def verify_magic_link(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify magic link token and return session credentials.
    
    URL: /auth/verify?token=<magic_link_token>
    """
    auth = AuthService(db)
    user = await auth.verify_magic_link(token)
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired magic link token",
        )
    
    # Create session token
    session_token = create_session_token(user.id, user.email, user.display_name)
    
    return VerifyResponse(
        token=session_token,
        user_id=user.id,
        email=user.email,
        name=user.display_name,
    )


@router.post("/update-name", response_model=UserResponse)
async def update_name(
    data: UpdateNameRequest,
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's display name."""
    auth = AuthService(db)
    user = await auth.update_user_name(current_user["sub"], data.name)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.display_name,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user info."""
    auth = AuthService(db)
    user = await auth.get_user_by_id(current_user["sub"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.display_name,
    )