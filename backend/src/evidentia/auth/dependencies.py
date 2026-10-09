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


DEFAULT_DEMO_USERS: list[dict[str, str]] = [
    {
        "email": "admin@tvn.com",
        "nombre": "Super Admin / Jurado",
        "password": "EvidentIA2026!",
        "role": "Super Admin",
        "org_id": "TVN Media",
    },
    {
        "email": "editor@tvn.com",
        "nombre": "Editor Jefe",
        "password": "EvidentIA2026!",
        "role": "Owner",
        "org_id": "TVN Media",
    },
    {
        "email": "periodista@tvn.com",
        "nombre": "Periodista de Redacción",
        "password": "EvidentIA2026!",
        "role": "Member",
        "org_id": "TVN Media",
    },
    {
        "email": "admin@vertexdc.com",
        "nombre": "Pedro Carreras",
        "password": "EvidentIA2026!",
        "role": "Super Admin",
        "org_id": "VERTEXdc",
    },
]


def bootstrap_initial_admin(session: Session) -> models.User | None:
    """Bootstrap or synchronize initial Super Admin and demo accounts for jury audit."""
    settings = get_settings()

    # 1. Synchronize all standard demo accounts
    created_or_updated: dict[str, models.User] = {}
    for demo in DEFAULT_DEMO_USERS:
        user = session.exec(select(models.User).where(models.User.email == demo["email"])).first()
        if user is None:
            user = models.User(
                email=demo["email"],
                nombre=demo["nombre"],
                hashed_password=hash_password(demo["password"]),
                role=demo["role"],
                org_id=demo["org_id"],
                is_active=True,
            )
            session.add(user)
        else:
            changed = False
            if not verify_password(demo["password"], user.hashed_password):
                user.hashed_password = hash_password(demo["password"])
                changed = True
            if user.role != demo["role"]:
                user.role = demo["role"]
                changed = True
            if not user.is_active:
                user.is_active = True
                changed = True
            if changed:
                session.add(user)
        created_or_updated[demo["email"]] = user

    # 2. Synchronize additional admin if specified in env/settings (e.g. admin@vertexdc.com)
    if settings.admin_email and settings.admin_email not in created_or_updated:
        env_admin = session.exec(select(models.User).where(models.User.email == settings.admin_email)).first()
        if env_admin is None:
            env_admin = models.User(
                email=settings.admin_email,
                nombre=settings.admin_initial_name,
                hashed_password=hash_password(settings.admin_password),
                role=settings.admin_initial_role,
                org_id=settings.admin_initial_org,
                is_active=True,
            )
            session.add(env_admin)
        else:
            if not verify_password(settings.admin_password, env_admin.hashed_password):
                env_admin.hashed_password = hash_password(settings.admin_password)
                session.add(env_admin)
        created_or_updated[settings.admin_email] = env_admin

    session.commit()
    for u in created_or_updated.values():
        session.refresh(u)

    # Return primary super admin
    return created_or_updated.get("admin@tvn.com") or created_or_updated.get(settings.admin_email)


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
