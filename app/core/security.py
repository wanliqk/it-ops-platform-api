import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

try:
    from passlib.context import CryptContext
except ImportError:  # pragma: no cover - dependency is declared for application runtime
    CryptContext = None

password_context = (
    CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext is not None else None
)
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    if password_context is None:
        raise RuntimeError("passlib[bcrypt] is required to hash passwords")
    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    if password_hash.startswith("$2") and password_context is not None:
        return password_context.verify(plain_password, password_hash)

    parts = password_hash.split("$")
    if parts[0] == "pbkdf2_sha256":
        return _verify_pbkdf2_sha256(plain_password, parts)

    return secrets.compare_digest(plain_password, password_hash)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expires_at = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None


def _verify_pbkdf2_sha256(plain_password: str, parts: list[str]) -> bool:
    if len(parts) == 2:
        return secrets.compare_digest(plain_password, parts[1])

    if len(parts) != 4:
        return False

    _, iterations, salt, expected_hash = parts
    try:
        decoded_iterations = int(iterations)
    except ValueError:
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode(),
        salt.encode(),
        decoded_iterations,
    )
    candidates = {
        base64.b64encode(derived).decode().strip(),
        derived.hex(),
    }
    return any(secrets.compare_digest(candidate, expected_hash) for candidate in candidates)
