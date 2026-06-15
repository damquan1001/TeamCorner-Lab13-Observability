from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app
from app.pii import hash_user_id


def _api_records(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("service") == "api"
    ]


def test_generates_request_id_header() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert re.fullmatch(r"req-[0-9a-f]{8}", response.headers["x-request-id"])
    assert float(response.headers["x-response-time-ms"]) >= 0


def test_echoes_incoming_request_id_header() -> None:
    with TestClient(app) as client:
        response = client.get("/health", headers={"x-request-id": "req-custom123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-custom123"


def test_dashboard_contains_required_six_panels() -> None:
    with TestClient(app) as client:
        response = client.get("/dashboard")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    for panel_id in [
        "panel-latency",
        "panel-traffic",
        "panel-errors",
        "panel-cost",
        "panel-tokens",
        "panel-quality",
    ]:
        assert f'data-panel="{panel_id}"' in html
    assert "setInterval(loadMetrics, 15000)" in html
    assert "SLO" in html


def test_chat_logs_are_enriched_and_scrubbed(tmp_path, monkeypatch) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)
    monkeypatch.setenv("APP_ENV", "test")

    payload = {
        "user_id": "u-secret",
        "session_id": "s-test",
        "feature": "qa",
        "message": "Email student@vinuni.edu.vn, phone 0987654321, card 4111 1111 1111 1111",
    }

    with TestClient(app) as client:
        response = client.post("/chat", json=payload, headers={"x-request-id": "req-testcase"})

    assert response.status_code == 200

    records = _api_records(log_path)
    assert records
    for record in records:
        assert record["correlation_id"] == "req-testcase"
        assert record["user_id_hash"] == hash_user_id("u-secret")
        assert record["session_id"] == "s-test"
        assert record["feature"] == "qa"
        assert record["model"] == "claude-sonnet-4-5"
        assert record["env"] == "test"

    raw_logs = log_path.read_text(encoding="utf-8")
    assert "student@" not in raw_logs
    assert "0987654321" not in raw_logs
    assert "4111" not in raw_logs
    assert "u-secret" not in raw_logs
