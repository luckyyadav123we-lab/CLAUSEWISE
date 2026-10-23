# CLAUSE-WISE

Evidence-first contract review support for founders, operators, and reviewers. This workspace contains a Vite/React frontend and FastAPI backend.

## Current capabilities

- Responsive landing page with an interactive, reduced-motion-aware product visual and an explicitly illustrative sample agreement.
- PDF, DOCX, and UTF-8 TXT extraction, plus pasted text (5 MB default limit; configurable with `MAX_UPLOAD_MB`). Scanned PDFs are rejected because OCR is not included.
- Deterministic offline clause checks, notice-period cross-checks, evidence excerpts, reviewer status updates, and PDF report export.
- SQLite persistence for analysis records and review decisions. Configure its location with `CLAUSEWISE_DB_PATH`.
- API health reports that persistence is SQLite and authentication is not configured.

## Important limitations

This is a functional local MVP, not a production-ready multi-user service. Authentication, per-user authorization, private object storage, background jobs, live LLM analysis, configurable retention, and account deletion are not implemented. The API currently serves records without user ownership checks. Do not deploy it publicly or upload sensitive contracts. Offline findings use deterministic patterns and may miss context or produce false positives; they are not legal advice.

The app must not be described as providing AI analysis: the available analysis mode is offline and rule-based. The login screen is a demo-only entry point; it does not verify credentials.

## Run locally

### Backend (Python 3.11+)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`.

### Frontend (Node 20+)

```powershell
cd frontend
pnpm install
Copy-Item .env.example .env
pnpm dev
```

Open `http://localhost:5173`. Set `VITE_API_BASE_URL` to the backend API base if needed. Set backend `CORS_ORIGINS` to the frontend origin. The SQLite database is created automatically; set `CLAUSEWISE_DB_PATH` to store it outside the source tree.

## API overview

- `GET /api/v1/health`
- `POST /api/v1/analyze` (multipart text or PDF/DOCX/TXT upload; offline mode only)
- `GET /api/v1/analysis` and `GET /api/v1/analysis/{id}`
- `GET /api/v1/analysis/{id}/clauses`, `/conflicts`, `/graph`
- `POST /api/v1/analysis/{id}/reviews`
- `POST /api/v1/analysis/{id}/export`
- `DELETE /api/v1/analysis/{id}`

No LLM credentials or Supabase configuration are used or required by the current implementation. Authentication and private storage should be added before enabling real customer data or public deployment.

## Verification

```powershell
cd backend
python -m pytest
cd ../frontend
pnpm build
```
