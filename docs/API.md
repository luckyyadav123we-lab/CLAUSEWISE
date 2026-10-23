# API

API prefix: `/api/v1`.

- `GET /health` reports service availability and offline mode.
- `POST /analyze` accepts multipart `text`, `filename`, `mode`, and optional `file`.
- `GET /analysis/{id}` returns the full analysis.
- `GET /analysis/{id}/clauses` returns scored clauses.
- `GET /analysis/{id}/conflicts` returns cross-clause findings.
- `GET /analysis/{id}/graph` returns relationship nodes and edges.
- `POST /analysis/{id}/reviews` records a finding review decision.
- `POST /analysis/{id}/rewrite` returns a limitation message for offline mode.
- `POST /analysis/{id}/compare` returns a unified text diff against an uploaded version.
- `POST /analysis/{id}/export` downloads a PDF review report.

Interactive schema: `/docs`.
