"""
RelateFX — Auth endpoints: signup, login, me
"""
import os
import secrets
import uuid
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import async_session
from models import User
from auth import hash_password, verify_password, create_access_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    token: str
    user_id: str
    name: str


@router.post("/signup", response_model=TokenResponse)
async def signup(req: SignupRequest):
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == req.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            id=uuid.uuid4().hex[:12],
            email=req.email,
            hashed_password=hash_password(req.password),
            name=req.name,
        )
        db.add(user)
        await db.commit()
        token = create_access_token(user.id, user.email)
        return TokenResponse(token=token, user_id=user.id, name=user.name)


@router.post("/admin-login", response_model=TokenResponse)
async def admin_login(req: AdminLoginRequest):
    admin_email = os.environ.get("ADMIN_EMAIL") or os.environ.get("ADMIN_USERNAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    admin_name = os.environ.get("ADMIN_NAME", "Admin")

    if not admin_email or not admin_password:
        raise HTTPException(status_code=503, detail="Admin login is not configured")

    email_matches = secrets.compare_digest(req.email.lower(), admin_email.lower())
    password_matches = secrets.compare_digest(req.password, admin_password)
    if not email_matches or not password_matches:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        user_id="admin",
        email=admin_email,
        name=admin_name,
        role="admin",
    )
    return TokenResponse(token=token, user_id="admin", name=admin_name)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == req.email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(user.id, user.email)
        return TokenResponse(token=token, user_id=user.id, name=user.name)


@router.get("/me")
async def get_me(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = authorization.split("Bearer ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("role") == "admin":
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name", "Admin"),
            "role": "admin",
        }
    user_id = payload.get("sub")
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user_id": user.id, "email": user.email, "name": user.name}
