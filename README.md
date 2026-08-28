# Multi-Agent Data Insight

Privacy-safe demo of a multi-agent analytics platform built with FastAPI and Vue 3.

The system turns structured CSV/JSON data into a traceable analysis workflow: an orchestrator delegates to specialized agents, an independent reviewer checks the result, and a prompt optimizer produces an actionable follow-up. The public edition uses synthetic data and user-provided model credentials only.

## What it demonstrates

- Multi-agent orchestration with specialized analysis and review agents
- Structured LLM outputs with prompt versioning and validation
- Data import, KPI aggregation, trend analysis, tagging, and report generation
- FastAPI backend with a Vue 3 dashboard
- Local SQLite persistence and API documentation

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # Windows: Copy-Item .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload
```

Open <http://127.0.0.1:8003/docs> for the API documentation. The Vue frontend lives in `web/` and runs with `npm install && npm run dev`.

## Scope and limitations

This is a portfolio-oriented demo, not a production advertising or customer-data system. It excludes company integrations, real datasets, internal thresholds, account credentials, and proprietary business rules. Production use requires authentication, authorization, rate limiting, audit logging, monitoring, and a dependency/license review.

Read [OPEN_SOURCE_READINESS.md](OPEN_SOURCE_READINESS.md) before publishing. Confirm permission to publish the source, prompts, UI assets, and derived materials.

