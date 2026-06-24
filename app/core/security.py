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
MD5_PREFIX = "md5$"
MD5_HEX_LENGTH = 32


def hash_password(password: str) -> str:
    return f"{MD5_PREFIX}{_md5_hex(password)}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    if password_hash.startswith(MD5_PREFIX):
        expected = password_hash.removeprefix(MD5_PREFIX)
        return secrets.compare_digest(_md5_hex(plain_password), expected)

    if _looks_like_md5_hex(password_hash):
        return secrets.compare_digest(_md5_hex(plain_password), password_hash.lower())

    if password_hash.startswith("$2") and password_context is not None:
        try:
            return password_context.verify(plain_password, password_hash)
        except ValueError:
            return False

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


def _md5_hex(password: str) -> str:
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def _looks_like_md5_hex(password_hash: str) -> bool:
    return len(password_hash) == MD5_HEX_LENGTH and all(
        char in "0123456789abcdefABCDEF" for char in password_hash
    )


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