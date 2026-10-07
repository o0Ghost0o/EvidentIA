"""FastAPI dependencies for authentication and RBAC."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session, select

from evidentia import models
from evidentia.auth.security import decode_token, hash_password, verify_password
from evidentia.config import get_settings
from evidentia.db import SessionDep

security_bearer = HTTPBearer(auto_error=False)

ROLE_HIERARCHY: dict[str, int] = {
    "Member": 1,
    "Admin": 2,
    "Owner": 3,
    "Super Admin": 4,
}


def bootstrap_initial_admin(session: Session) -> models.User | None:
    """Bootstrap or synchronize initial Super Admin user from secrets / environment."""
    settings = get_settings()
    admin = session.exec(select(models.User).where(models.User.email == settings.admin_email)).first()
    if admin is not None:
        if not verify_password(settings.admin_password, admin.hashed_password):
            admin.hashed_password = hash_password(settings.admin_password)
            session.add(admin)
            session.commit()
            session.refresh(admin)
        return admin

    admin = models.User(
        email=settings.admin_email,
        nombre=settings.admin_initial_name,
        hashed_password=hash_password(settings.admin_password),
        role=settings.admin_initial_role,
        org_id=settings.admin_initial_org,
        is_active=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_bearer)],
    session: SessionDep,
) -> models.User:
    """Validate access token and return the authenticated User."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type (expected access token)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = session.get(models.User, int(user_id))
    except (ValueError, TypeError):
        user = None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_bearer)],
    session: SessionDep,
) -> models.User | None:
    """Optionally validate token and return User if authenticated, else None."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = session.get(models.User, int(user_id))
        return user if user and user.is_active else None
    except Exception:
        return None


def require_role(min_role: str) -> Callable:
    """Ensure the authenticated user has at least the required role in the RBAC hierarchy."""
    def role_checker(current_user: Annotated[models.User, Depends(get_current_user)]) -> models.User:
        user_weight = ROLE_HIERARCHY.get(current_user.role, 0)
        required_weight = ROLE_HIERARCHY.get(min_role, 0)
        if user_weight < required_weight:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: requires at least '{min_role}' role (current role is '{current_user.role}')",
            )
        return current_user

    return role_checker
