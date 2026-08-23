import pytest
from tests.conftest import login

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_register_login_me(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"phone": "+79009999999", "email": "new@example.com", "password": "Password123!", "full_name": "Test"},
    )
    assert r.status_code == 201
    r = await client.post("/api/v1/auth/login", json={"email": "new@example.com", "password": "Password123!"})
    assert r.status_code == 200
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = await client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200 and r.json()["role"] == "driver"


async def test_wrong_password_rate_limited_path(client):
    r = await client.post("/api/v1/auth/login", json={"email": "driver@example.com", "password": "bad"})
    assert r.status_code == 401


async def test_stations_filters(client):
    r = await client.get("/api/v1/stations", params={"q": ""})
    assert r.status_code == 200
    assert len(r.json()) >= 2
    r = await client.get("/api/v1/stations", params={"power": ["p22"]})
    assert all(s["max_power_kw"] >= 22.0 for s in r.json())


async def test_full_charging_flow(client, driver_headers):
    stations = (await client.get("/api/v1/stations")).json()
    station_id = next(s["id"] for s in stations if s["status"] == "available")
    quote = await client.post(
        "/api/v1/charging-sessions/quote",
        headers=driver_headers,
        json={"station_id": station_id, "limit_type": "kwh", "limit_value": 10},
    )
    assert quote.status_code == 200
    q = quote.json()
    assert q["estimated_kwh"] == 10.00 or float(q["estimated_kwh"]) >= 10
    start = await client.post(
        "/api/v1/charging-sessions/start",
        headers=driver_headers,
        json={"station_id": station_id, "limit_type": "kwh", "limit_value": 10},
    )
    assert start.status_code == 201
    sid = start.json()["id"]
    payment_create = await client.post(
        "/api/v1/payments/create",
        headers=driver_headers,
        json={"session_id": sid, "method": "sbp_qr"},
    )
    assert payment_create.status_code == 200
    pid = payment_create.json()["payment"]["id"]
    assert payment_create.json()["confirmation"]["sbp_payload"].startswith("https://qr.nspk.ru/")
    from app.db.session import SessionLocal
    from app.models.hardware import StationCommand
    from sqlalchemy import select

    async with SessionLocal() as db:
        cmds = (await db.execute(select(StationCommand).where(StationCommand.payload.op("->>")("session_id") == sid))).scalars().all()
        assert all(c.type != "start" for c in cmds)
    simulate_success_webhook = await client.post(f"/api/v1/payments/mock/{pid}/simulate-success", headers=driver_headers)
    assert simulate_success_webhook.status_code == 200
    async with SessionLocal() as db:
        cmds = (await db.execute(select(StationCommand).where(StationCommand.payload.op("->>")("session_id") == sid))).scalars().all()
        assert any(c.type == "start" for c in cmds)
    import asyncio

    await asyncio.sleep(3)
    r = await client.get(f"/api/v1/charging-sessions/{sid}", headers=driver_headers)
    assert r.json()["status"] in ["preparing", "charging"]
    r = await client.post(f"/api/v1/charging-sessions/{sid}/stop", headers=driver_headers)
    assert r.status_code == 200
    await asyncio.sleep(3)
    r = await client.get(f"/api/v1/charging-sessions/{sid}", headers=driver_headers)
    body = r.json()
    assert body["status"] == "completed" and body["stop_reason"] == "user"
    r = await client.get(f"/api/v1/payments/{pid}/receipt", headers=driver_headers)
    assert r.status_code == 200 and r.json()["number"].startswith("RCP-")


async def test_rbac_operator_denied_for_driver(client, driver_headers):
    r = await client.get("/api/v1/operator/stats", headers=driver_headers)
    assert r.status_code == 403
