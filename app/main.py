from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import record_error, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .tracing import tracing_enabled

configure_logging()
log = get_logger()
app = FastAPI(title="Day 13 Observability Lab")
app.add_middleware(CorrelationIdMiddleware)
agent = LabAgent()


@app.on_event("startup")
async def startup() -> None:
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "day13-observability-lab"),
        env=os.getenv("APP_ENV", "dev"),
        payload={"tracing_enabled": tracing_enabled()},
    )


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "tracing_enabled": tracing_enabled(), "incidents": status()}


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Day 13 Observability Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --line: #d8dde6;
      --text: #1f2933;
      --muted: #5d6979;
      --accent: #0f766e;
      --warn: #b45309;
      --danger: #b91c1c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      padding: 18px 24px 12px;
      border-bottom: 1px solid var(--line);
      background: #fff;
    }
    h1 { margin: 0; font-size: 20px; font-weight: 650; letter-spacing: 0; }
    .meta { margin-top: 6px; color: var(--muted); font-size: 13px; }
    main {
      padding: 18px 24px 28px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 14px;
    }
    section {
      min-height: 168px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    h2 { margin: 0 0 12px; font-size: 15px; font-weight: 650; letter-spacing: 0; }
    .value { font-size: 30px; font-weight: 700; line-height: 1.1; }
    .unit { color: var(--muted); font-size: 13px; margin-left: 4px; }
    .rows { display: grid; gap: 8px; }
    .row { display: flex; justify-content: space-between; gap: 12px; font-size: 14px; }
    .label { color: var(--muted); }
    .threshold {
      margin-top: 12px;
      border-top: 1px solid var(--line);
      padding-top: 10px;
      color: var(--muted);
      font-size: 12px;
    }
    .ok { color: var(--accent); }
    .warn { color: var(--warn); }
    .danger { color: var(--danger); }
  </style>
</head>
<body>
  <header>
    <h1>Day 13 Observability Dashboard</h1>
    <div class="meta">Default range: last 1 hour · Auto refresh: 15 seconds · Source: /metrics</div>
  </header>
  <main>
    <section data-panel="panel-latency">
      <h2>Latency P50 / P95 / P99</h2>
      <div class="rows">
        <div class="row"><span class="label">P50</span><strong id="latency-p50">0 ms</strong></div>
        <div class="row"><span class="label">P95</span><strong id="latency-p95">0 ms</strong></div>
        <div class="row"><span class="label">P99</span><strong id="latency-p99">0 ms</strong></div>
      </div>
      <div class="threshold">SLO: P95 &lt; 3000 ms, alert at &gt; 5000 ms for 30m</div>
    </section>
    <section data-panel="panel-traffic">
      <h2>Traffic</h2>
      <div><span id="traffic" class="value">0</span><span class="unit">requests</span></div>
      <div class="threshold">SLO input: enough sampled requests to inspect behavior</div>
    </section>
    <section data-panel="panel-errors">
      <h2>Error Rate & Breakdown</h2>
      <div><span id="error-rate" class="value ok">0%</span><span class="unit">current</span></div>
      <div id="error-breakdown" class="threshold">No errors recorded</div>
    </section>
    <section data-panel="panel-cost">
      <h2>Cost</h2>
      <div><span id="total-cost" class="value">$0.0000</span><span class="unit">total</span></div>
      <div class="threshold">SLO: daily cost &lt; $2.50, alert on hourly spike &gt; 2x baseline</div>
    </section>
    <section data-panel="panel-tokens">
      <h2>Tokens In / Out</h2>
      <div class="rows">
        <div class="row"><span class="label">Input</span><strong id="tokens-in">0</strong></div>
        <div class="row"><span class="label">Output</span><strong id="tokens-out">0</strong></div>
      </div>
      <div class="threshold">Units: tokens, cumulative for current app process</div>
    </section>
    <section data-panel="panel-quality">
      <h2>Quality Proxy</h2>
      <div><span id="quality" class="value">0.00</span><span class="unit">avg score</span></div>
      <div class="threshold">SLO: average quality score &gt;= 0.75</div>
    </section>
  </main>
  <script>
    const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
    function pct(part, total) {
      return total ? `${fmt.format((part / total) * 100)}%` : "0%";
    }
    async function loadMetrics() {
      const response = await fetch("/metrics", { cache: "no-store" });
      const m = await response.json();
      const errors = Object.values(m.error_breakdown || {}).reduce((a, b) => a + b, 0);
      document.getElementById("latency-p50").textContent = `${fmt.format(m.latency_p50)} ms`;
      document.getElementById("latency-p95").textContent = `${fmt.format(m.latency_p95)} ms`;
      document.getElementById("latency-p99").textContent = `${fmt.format(m.latency_p99)} ms`;
      document.getElementById("traffic").textContent = fmt.format(m.traffic);
      document.getElementById("error-rate").textContent = pct(errors, m.traffic);
      document.getElementById("error-breakdown").textContent = errors
        ? JSON.stringify(m.error_breakdown)
        : "No errors recorded";
      document.getElementById("total-cost").textContent = `$${Number(m.total_cost_usd).toFixed(4)}`;
      document.getElementById("tokens-in").textContent = fmt.format(m.tokens_in_total);
      document.getElementById("tokens-out").textContent = fmt.format(m.tokens_out_total);
      document.getElementById("quality").textContent = Number(m.quality_avg).toFixed(2);
    }
    loadMetrics();
    setInterval(loadMetrics, 15000);
  </script>
</body>
</html>
"""


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    bind_contextvars(
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id,
        feature=body.feature,
        model=agent.model,
        env=os.getenv("APP_ENV", "dev"),
    )
    
    log.info(
        "request_received",
        service="api",
        payload={"message_preview": summarize_text(body.message)},
    )
    try:
        result = agent.run(
            user_id=body.user_id,
            feature=body.feature,
            session_id=body.session_id,
            message=body.message,
        )
        log.info(
            "response_sent",
            service="api",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            payload={"answer_preview": summarize_text(result.answer)},
        )
        return ChatResponse(
            answer=result.answer,
            correlation_id=request.state.correlation_id,
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            quality_score=result.quality_score,
        )
    except Exception as exc:  # pragma: no cover
        error_type = type(exc).__name__
        record_error(error_type)
        log.error(
            "request_failed",
            service="api",
            error_type=error_type,
            payload={"detail": str(exc), "message_preview": summarize_text(body.message)},
        )
        raise HTTPException(status_code=500, detail=error_type) from exc


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
