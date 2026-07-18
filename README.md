# CCMed — Adaptive K-12 Mastery Engine

A MATATAG-aligned adaptive practice engine: FastAPI backend, React/Vite frontend, Postgres (Neon) storage, deployed on Google Cloud Run + Firebase Hosting.

## Start here

- **Working on the practice problem generator (pg pipeline)?** Read [`docs/pgen_contract.md`](docs/pgen_contract.md) first — it's the binding contract, and `python -m backend.app.practice_gen.validation.run_all` exiting 0 is the definition of done.
- **Writing or restructuring any doc in `docs/`?** Read [`docs/DOC_RULES.md`](docs/DOC_RULES.md) first — every agent-facing doc must be classified as a contract, judgment guide, or explainer.
- **Setting up infra, CI/CD, or deployment?** See [`docs/INFRASTRUCTURE_WORKFLOW.md`](docs/INFRASTRUCTURE_WORKFLOW.md).
- **Running as an autonomous agent in this repo?** See [`docs/AGENT_ENVIRONMENT.md`](docs/AGENT_ENVIRONMENT.md) for the Graphify/MCP workflow, and `AGENTS.md` (symlinked as `CLAUDE.md`) for engineering protocols.

## Layout

| Path | Purpose |
|---|---|
| `backend/app/practice_gen/` | The practice problem generator: DNA (concept generators), formatters, compatibility tables, orchestrator. |
| `backend/app/practice_gen/validation/` | The pg harness (`run_all` is the entry point). Read-only unless your task is building/fixing the harness itself. |
| `backend/app/routes/` | FastAPI route handlers (MATATAG Lab, student portal, parent dashboard). |
| `frontend/` | React/Vite app — MATATAG Lab, student portal, parent dashboard UI. |
| `data/knowledge_graph_g1_3.json` | The MATATAG curriculum knowledge graph (grades 1–3): vocab, concepts, competency bounds. |
| `docs/` | Contract / judgment / explainer docs. Classify before adding — see `DOC_RULES.md`. |
| `tests/` | Supplementary auditors and regression tests (not the primary harness). |
| `validation_reports/` | Harness output: matrix reports, judgment evidence, hardening evidence log. |

## Definition of done (pg pipeline)

```bash
python -m backend.app.practice_gen.validation.run_all   # exits 0
```

See [`docs/pgen_contract.md`](docs/pgen_contract.md) for the full rule table and [`AGENTS.md`](AGENTS.md) for engineering protocols.
