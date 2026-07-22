"""
====================================================
Security Module
====================================================
JWT validation, password hashing, and Supabase auth.
====================================================
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationException, AuthorizationException

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


# ====================================================
# Password Hashing
# ====================================================
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ====================================================
# JWT Tokens
# ====================================================
def create_access_token(
    subject: str | Any,
    claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    if claims:
        to_encode.update(claims)

    return jwt.encode(to_encode, settings.SUPABASE_JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Token has expired", error_code="token_expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationException(f"Invalid token: {e}", error_code="invalid_token")


# ====================================================
# Supabase Token Validation
# ====================================================
def validate_supabase_token(token: str) -> dict[str, Any]:
    """
    Validate a JWT token — accepts both Supabase-issued and
    backend-issued tokens.
    """
    # Try Supabase token (aud=authenticated, no issuer check)
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
        )
        return payload
    except jwt.InvalidTokenError:
        pass

    # Try backend-issued token (aud + iss)
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Token expired", error_code="token_expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationException(f"Invalid token: {e}", error_code="invalid_token")


# ====================================================
# Role-Based Access Control (RBAC)
# ====================================================
class Role:
    """User roles."""
    ADMIN = "admin"
    OFFICER = "officer"
    ANALYST = "analyst"


# Role hierarchy: higher index = more privileges
ROLE_HIERARCHY = {
    Role.ANALYST: 1,
    Role.OFFICER: 2,
    Role.ADMIN: 3,
}


def has_role(user_role: str, required_role: str) -> bool:
    """Check if a user's role meets the required level."""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 99)
    return user_level >= required_level


def require_role(user_role: str, required_role: str) -> None:
    """Raise if user doesn't have required role."""
    if not has_role(user_role, required_role):
        raise AuthorizationException(
            f"Role '{required_role}' required, but user has '{user_role}'",
            error_code="insufficient_role",
        )
