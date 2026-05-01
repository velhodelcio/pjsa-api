from fastapi.testclient import TestClient

from app.main import create_app


def test_health() -> None:
    app = create_app()
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_v1_ping() -> None:
    app = create_app()
    client = TestClient(app)
    r = client.get("/api/v1/ping")
    assert r.status_code == 200
    assert r.json() == {"message": "pong"}
