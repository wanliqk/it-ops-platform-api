from datetime import timedelta

from app.core.security import create_access_token, decode_access_token, verify_password


def test_verify_placeholder_pbkdf2_password() -> None:
    assert verify_password("test_admin_password", "pbkdf2_sha256$test_admin_password")


def test_create_and_decode_access_token() -> None:
    token = create_access_token("1", expires_delta=timedelta(minutes=5))

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "1"
