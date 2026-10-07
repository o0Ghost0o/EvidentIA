"""Authentication endpoints: login, token refresh rotation, profile, and logout."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import select

from evidentia import models
from evidentia.auth.dependencies import (
    bootstrap_initial_admin,
    get_current_user,
    require_role,
)
from evidentia.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from evidentia.config import get_settings
from evidentia.db import SessionDep

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class UserResponse(BaseModel):
    id: int
    email: str
    nombre: str
    role: str
    org_id: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds
    refresh_expires_in: int = 604800  # 7 days in seconds
    user: UserResponse


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6)
    nombre: str = Field(default="", max_length=128)
    role: str = Field(default="Member")
    org_id: str = Field(default="VERTEXdc")


def _format_user(user: models.User) -> UserResponse:
    return UserResponse(
        id=user.id or 0,
        email=user.email,
        nombre=user.nombre,
        role=user.role,
        org_id=user.org_id,
        is_active=user.is_active,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: SessionDep) -> TokenResponse:
    """Authenticate and issue 15-minute access token and 7-day refresh token."""
    # Ensure bootstrap admin exists if database has no users
    bootstrap_initial_admin(session)

    user = session.exec(select(models.User).where(models.User.email == payload.email)).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # 15m Access Token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "org_id": user.org_id}
    )

    # 7d Refresh Token
    raw_refresh, token_h, expires_at = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )

    # Store refresh token record for tracking and rotation
    db_token = models.RefreshToken(
        user_id=user.id,
        token_hash=token_h,
        expires_at=expires_at,
        revoked=False,
    )
    session.add(db_token)
    session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        user=_format_user(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, session: SessionDep) -> TokenResponse:
    """Rotate refresh token: revoke old token and return a fresh 15m access token + 7d refresh token."""
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type (expected refresh token)",
        )

    token_h = hash_token(payload.refresh_token)
    now = datetime.now(timezone.utc)

    # Look up refresh token in DB
    db_token = session.exec(
        select(models.RefreshToken).where(
            models.RefreshToken.token_hash == token_h,
            models.RefreshToken.revoked == False,  # noqa: E712
            models.RefreshToken.expires_at > now,
        )
    ).first()

    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked, expired, or does not exist",
        )

    user = session.get(models.User, db_token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Token Rotation: invalidate previous refresh token
    db_token.revoked = True
    session.add(db_token)

    # Issue new 15m access token and new 7d refresh token
    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role, "org_id": user.org_id}
    )
    new_raw_refresh, new_token_h, new_expires_at = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )

    new_db_token = models.RefreshToken(
        user_id=user.id,
        token_hash=new_token_h,
        expires_at=new_expires_at,
        revoked=False,
    )
    session.add(new_db_token)
    session.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_raw_refresh,
        user=_format_user(user),
    )


@router.post("/logout", status_code=204)
def logout(payload: RefreshRequest, session: SessionDep) -> None:
    """Revoke a refresh token on logout."""
    token_h = hash_token(payload.refresh_token)
    db_token = session.exec(
        select(models.RefreshToken).where(models.RefreshToken.token_hash == token_h)
    ).first()
    if db_token:
        db_token.revoked = True
        session.add(db_token)
        session.commit()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[models.User, Depends(get_current_user)]) -> UserResponse:
    """Return the profile and role of the currently authenticated user."""
    return _format_user(current_user)


@router.post("/bootstrap", response_model=UserResponse)
def bootstrap(session: SessionDep) -> UserResponse:
    """Ensure the default Super Admin from secrets / environment exists."""
    admin = bootstrap_initial_admin(session)
    if admin is None:
        raise HTTPException(status_code=500, detail="Could not bootstrap admin user")
    return _format_user(admin)


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    payload: RegisterRequest,
    session: SessionDep,
    current_user: Annotated[models.User, Depends(require_role("Admin"))],
) -> UserResponse:
    """Register a new user (restricted to Admin or higher)."""
    existing = session.exec(select(models.User).where(models.User.email == payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    user = models.User(
        email=payload.email,
        nombre=payload.nombre,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        org_id=payload.org_id,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _format_user(user)
