from __future__ import annotations

from pathlib import Path

import yaml


def test_alert_rules_have_runbooks_and_individual_owner() -> None:
    config = yaml.safe_load(Path("config/alert_rules.yaml").read_text(encoding="utf-8"))
    alerts = config["alerts"]

    assert len(alerts) >= 3
    names = {alert["name"] for alert in alerts}
    assert {"high_latency_p95", "high_error_rate", "cost_budget_spike"}.issubset(names)

    runbook = Path("docs/alerts.md").read_text(encoding="utf-8")
    for alert in alerts:
        assert alert["owner"] == "individual-owner"
        assert alert["type"] == "symptom-based"
        assert alert["runbook"].startswith("docs/alerts.md#")
        anchor = alert["runbook"].split("#", 1)[1].replace("-", " ").lower()
        assert all(part in runbook.lower() for part in anchor.split())
