import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import settings


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    parts = password_hash.split("$")
    if parts[0] == "pbkdf2_sha256":
        return _verify_pbkdf2_sha256(plain_password, parts)

    return secrets.compare_digest(plain_password, password_hash)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expires_at = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": int(expires_at.timestamp())}
    encoded_payload = _urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(encoded_payload)
    return f"{encoded_payload}.{signature}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        encoded_payload, signature = token.split(".", maxsplit=1)
    except ValueError:
        return None

    if not secrets.compare_digest(_sign(encoded_payload), signature):
        return None

    padded_payload = encoded_payload + "=" * (-len(encoded_payload) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode()))
    except (ValueError, json.JSONDecodeError):
        return None

    if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
        return None

    return payload


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


def _sign(value: str) -> str:
    digest = hmac.new(settings.secret_key.encode(), value.encode(), hashlib.sha256).digest()
    return _urlsafe_b64encode(digest)


def _urlsafe_b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")
