# Day 13 Observability Lab Template

Individual repo for a 4-hour hands-on lab on Monitoring, Logging, and Observability.

## What students will build

A small FastAPI "agent" instrumented with:
- structured JSON logging
- correlation ID propagation
- PII scrubbing
- Langfuse tracing
- minimal metrics aggregation
- SLOs, alerts, and a blueprint report

This template started as a gapped lab. The individual task is to complete the instrumentation, collect evidence, and submit one coherent report.

## Suggested lab flow (Gapped Template)

1. **Run the starter app**: Observe that logs are basic and correlation IDs are missing.
2. **Implement Correlation IDs**: Fix `app/middleware.py` so every request has a unique `x-request-id`.
3. **Enrich Logs**: Update `app/main.py` to bind user, session, and feature context to every log.
4. **Sanitize Data**: Implement the PII scrubber in `app/logging_config.py`.
5. **Verify with Script**: Run `python scripts/validate_logs.py` to check your progress.
6. **Tracing**: Send 10-20 requests and verify traces in Langfuse (ensure `observe` decorator is used).
7. **Dashboards**: Build your 6-panel dashboard from exported metrics.
8. **Alerting**: Configure alert rules in `config/alert_rules.yaml` and test them.

## Individual completion checklist

```bash
# Run automated tests
.\.venv\Scripts\python.exe -m pytest -q

# Start the app
uvicorn app.main:app --reload

# In another terminal, generate at least 10 requests
python scripts/load_test.py --concurrency 5

# Check JSON logs, correlation IDs, enrichment, and PII scrubbing
python scripts/validate_logs.py

# Open the 6-panel metrics dashboard
# http://127.0.0.1:8000/dashboard
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Tooling

```bash
# Generate requests (use --concurrency 5 to test parallel bottlenecks)
python scripts/load_test.py --concurrency 5

# Inject failures live
python scripts/inject_incident.py --scenario rag_slow

# Check your implementation progress
python scripts/validate_logs.py
```

## Repo map

```text
app/
  main.py                FastAPI app
  agent.py               core agent pipeline
  logging_config.py      structlog config
  middleware.py          correlation ID middleware
  pii.py                 scrubbing helpers
  tracing.py             Langfuse helpers
  schemas.py             request/response/log models
  metrics.py             in-memory metrics helpers
  incidents.py           toggles for injected failures
  mock_llm.py            deterministic fake LLM
  mock_rag.py            deterministic fake retrieval
config/
  slo.yaml               starter SLOs
  alert_rules.yaml       starter alerts
  logging_schema.json    expected log schema
scripts/
  load_test.py           generate requests
  inject_incident.py     flip incident toggles
  validate_logs.py       schema checks for logs
data/
  sample_queries.jsonl   requests for testing
  expected_answers.jsonl starter quality checks
  incidents.json         scenario descriptions
  logs.jsonl             app output target
  audit.jsonl            optional audit log output

docs/
  blueprint-template.md  individual submission template
  alerts.md              runbook + alert worksheet
  dashboard-spec.md      6-panel dashboard checklist
  grading-evidence.md    evidence collection sheet
  mock-debug-qa.md       oral/written debugging questions
```

## Individual work areas

- Logging, correlation IDs, and PII scrubbing
- Tracing tags and request metadata
- SLOs, alert rules, and runbooks
- Load testing, incident injection, dashboard evidence
- Blueprint report and demo evidence

## Grading policy

Your final grade is calculated as follows:

1. **Technical Implementation**: Verified by `validate_logs.py` and live system state.
2. **Incident Response**: Accuracy of your root cause analysis in the report.
3. **Live Demo / Evidence**: System demonstration, dashboard screenshots, and trace evidence.
4. **Individual Report & Git Evidence**: Quality of `docs/blueprint-template.md` and traceable commits.

**Passing Criteria**: 
- All implementation gaps must be completed.
- Minimum of 10 traces must be visible in Langfuse.
- Dashboard must show all 6 required panels.
