from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(admin_id: int, username: str, role: str) -> str:
    import uuid

    now = datetime.now(UTC)
    payload = {
        "jti": str(uuid.uuid4()),
        "sub": str(admin_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=settings.JWT_EXPIRE_HOURS),
        "iss": "mesh-auth-service",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并验证 JWT，抛出 jwt.PyJWTError 表示无效"""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["jti", "sub", "role", "exp"]},
    )


def decode_student_token(token: str) -> dict:
    """解码学生/家长 JWT（不要求 role 字段）"""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["jti", "sub", "exp"]},
    )


def create_student_access_token(student_id: int, user_type: str = "STUDENT") -> str:
    import uuid

    now = datetime.now(UTC)
    payload = {
        "jti": str(uuid.uuid4()),
        "sub": str(student_id),
        "user_type": user_type,
        "iat": now,
        "exp": now + timedelta(days=7),
        "iss": "mesh-auth-service",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_student_refresh_token(student_id: int) -> str:
    import uuid

    now = datetime.now(UTC)
    payload = {
        "jti": str(uuid.uuid4()),
        "sub": str(student_id),
        "token_type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=30),
        "iss": "mesh-auth-service",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
