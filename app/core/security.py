import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Literal
from jose import JWTError, jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from app.core.config import settings

ph = PasswordHasher(
    time_cost=2,        
    memory_cost=65536, 
    parallelism=2,      
    hash_len=32,
    salt_len=16,
)

def hash_password(plain: str) -> str:
    """Hash a plain text password using Argon2id."""
    return ph.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against Argon2 hash."""
    try:
        return ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False

def needs_rehash(hashed: str) -> bool:
    """Check if hash needs upgrading (e.g. after changing cost params)."""
    return ph.check_needs_rehash(hashed)


def create_token(
    subject: str,
    token_type: Literal["access", "refresh"],
    extra_data: dict = {},
) -> str:
    """Create a signed JWT token."""
    if token_type == "access":
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(subject),        # user id
        "type": token_type,
        "exp": expire,
        "iat": datetime.utcnow(),
        **extra_data,               # e.g. {"role": "admin"}
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

def create_token_pair(user_id: int, role: str) -> dict:
    """Create both access and refresh tokens at once."""
    return {
        "access_token":  create_token(str(user_id), "access",  {"role": role}),
        "refresh_token": create_token(str(user_id), "refresh", {"role": role}),
        "token_type":    "bearer",
    }