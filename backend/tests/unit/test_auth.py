import pytest

from app.core.auth import AuthError, verify_token, decode_token


def test_missing_token_raises():
    import asyncio
    with pytest.raises(AuthError, match="No token"):
        asyncio.run(verify_token(None))


def test_invalid_token_raises():
    import asyncio
    with pytest.raises(AuthError):
        asyncio.run(verify_token("short"))


def test_decode_token_with_bad_jwks():
    with pytest.raises(AuthError, match="Invalid token header"):
        decode_token("not-a-jwt", {"keys": []}, "audience")


def test_decode_token_missing_kid():
    # Create a token-like string that jose can parse header from
    # but has no kid
    import json
    import base64

    header = base64.urlsafe_b64encode(json.dumps({"alg": "RS256"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"sub": "test"}).encode()).decode().rstrip("=")
    sig = base64.urlsafe_b64encode(b"fake").decode().rstrip("=")
    fake_token = f"{header}.{payload}.{sig}"

    with pytest.raises(AuthError, match="missing kid"):
        decode_token(fake_token, {"keys": []}, "audience")
