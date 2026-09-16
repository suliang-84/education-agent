from app.core.response import fail, ok
from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_hash_and_verify():
    hashed = hash_password("qwer123#")
    assert verify_password("qwer123#", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_create_and_decode():
    token = create_access_token(1, "admin", "SUPER_ADMIN")
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["role"] == "SUPER_ADMIN"
    assert payload["username"] == "admin"


def test_response_ok():
    r = ok({"id": 1})
    assert r["status"] == "success"
    assert r["code"] == 0
    assert r["data"]["id"] == 1


def test_response_fail():
    r = fail("AUTH-001", "Token 无效")
    assert r["status"] == "fail"
    assert r["code"] == "AUTH-001"
    assert r["data"] is None
