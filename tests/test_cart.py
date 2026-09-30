import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    import os
    os.environ["DB_PATH"] = str(tmp_path_factory.mktemp("db") / "test.db")
    os.environ["LOG_FILE"] = str(tmp_path_factory.mktemp("log") / "test.log")
    from app.main import app
    with TestClient(app) as c:  # runs lifespan (init_db + MCP session manager)
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_add_list_remove(client):
    r = client.post("/api/cart", json={"name": "Shoes", "price": 999.5, "qty": 2})
    assert r.status_code == 200
    item_id = r.json()["id"]

    data = client.get("/api/cart").json()
    assert data["total"] == 1999.0
    assert any(i["id"] == item_id for i in data["items"])

    assert client.delete(f"/api/cart/{item_id}").status_code == 200
    assert client.delete(f"/api/cart/{item_id}").status_code == 404


def test_validation(client):
    r = client.post("/api/cart", json={"name": "Bad", "price": -5})
    assert r.status_code == 422


def test_metrics_and_page(client):
    assert b"http_requests_total" in client.get("/metrics").content
    assert "Shopping Cart" in client.get("/").text
