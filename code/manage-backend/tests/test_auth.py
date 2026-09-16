import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    resp = await client.post("/api/v1/admin/auth/login", json={
        "username": "admin",
        "password": "qwer123#"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "access_token" in data["data"]
    assert data["data"]["admin"]["username"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/v1/admin/auth/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert resp.status_code == 401
    data = resp.json()
    assert data["status"] == "fail"
    assert data["code"] == "LOGIN-001"


@pytest.mark.asyncio
async def test_login_wrong_username(client):
    resp = await client.post("/api/v1/admin/auth/login", json={
        "username": "notexist",
        "password": "qwer123#"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client):
    # 先登录拿 token
    login_resp = await client.post("/api/v1/admin/auth/login", json={
        "username": "admin",
        "password": "qwer123#"
    })
    token = login_resp.json()["data"]["access_token"]

    # 退出
    resp = await client.post(
        "/api/v1/admin/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


@pytest.mark.asyncio
async def test_protected_route_without_token(client):
    resp = await client.post("/api/v1/admin/auth/logout")
    # HTTPBearer 在没有 token 时返回 403 (旧版) 或 401 (新版 FastAPI)
    assert resp.status_code in (401, 403)
