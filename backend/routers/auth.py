"""
RelateFX — Auth endpoints: signup, login, me
"""
import uuid
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

import sys
import os
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
    user_id = payload.get("sub")
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user_id": user.id, "email": user.email, "name": user.name}