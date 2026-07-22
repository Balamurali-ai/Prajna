"""
====================================================
Core Package
====================================================
Cross-cutting concerns: config, logging, security.
====================================================
"""
from app.core.config import settings
from app.core.security import (
    Role,
    create_access_token,
    decode_token,
    hash_password,
    has_role,
    require_role,
    validate_supabase_token,
    verify_password,
)

__all__ = [
    "settings",
    "Role",
    "create_access_token",
    "decode_token",
    "hash_password",
    "has_role",
    "require_role",
    "validate_supabase_token",
    "verify_password",
]
