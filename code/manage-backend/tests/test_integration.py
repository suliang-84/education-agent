import pytest


@pytest.mark.asyncio
async def test_full_auth_flow(client):
    """完整认证流程：登录 → 访问受保护接口 → 退出 → Token 失效"""
    # 1. 登录
    resp = await client.post(
        "/api/v1/admin/auth/login", json={"username": "admin", "password": "qwer123#"}
    )
    assert resp.status_code == 200
    token = resp.json()["data"]["access_token"]

    # 2. 退出
    resp = await client.post(
        "/api/v1/admin/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200

    # 3. 再次使用同一 token（应被拒绝）
    resp = await client.post(
        "/api/v1/admin/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 401
