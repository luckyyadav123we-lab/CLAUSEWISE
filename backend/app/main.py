from datetime import datetime, timezone
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import sqlite3
from contextlib import contextmanager
from app.services.document_parser import extract_document, segment
from app.agents.offline import analyze
from app.services.risk_engine import score_clauses

app = FastAPI(title="CLAUSE-WISE API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in __import__("os").getenv("CORS_ORIGINS", "http://localhost:5173").split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
DB_PATH = os.getenv("CLAUSEWISE_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "clausewise.sqlite3"))
records: dict[str, dict] = {}

@contextmanager
def _db():
    db = sqlite3.connect(DB_PATH)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS analyses (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, filename TEXT NOT NULL, payload TEXT NOT NULL)")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def _persist(record: dict):
    with _db() as db:
        db.execute("INSERT OR REPLACE INTO analyses(id,created_at,filename,payload) VALUES(?,?,?,?)", (record["id"], record["created_at"], record["filename"], json.dumps(record)))

def _load_records():
    with _db() as db:
        records.update({row[0]: json.loads(row[1]) for row in db.execute("SELECT id,payload FROM analyses")})

_load_records()

class TextRequest(BaseModel):
    text: str
    filename: str = "Pasted contract"
    mode: str = "offline"
    perspective: str = "neutral"

class ReviewRequest(BaseModel):
    finding_id: str
    decision: str
    note: str = ""

def create_analysis(text: str, filename: str, mode: str):
    if not text.strip():
        raise HTTPException(400, "Add contract text before analysis.")
    clauses = segment(text)
    findings, conflicts = analyze(clauses)
    scored = score_clauses(clauses, findings)
    available = [c["risk_score"] for c in scored if c["risk_score"] is not None]
    aid = str(uuid4())
    result = {"id": aid, "filename": filename, "status": "completed", "mode": "offline", "created_at": datetime.now(timezone.utc).isoformat(), "clause_count": len(clauses), "overall_score": max(available) if available else None, "risk_level": "unavailable" if not available else ("low" if max(available) <= 3 else "medium" if max(available) <= 6 else "high"), "clauses": scored, "findings": findings, "conflicts": conflicts, "text": text, "reviews": []}
    records[aid] = result
    _persist(result)
    return result

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "analysis_modes": ["offline"], "persistence": "sqlite", "authentication": "not_configured"}

@app.get("/api/v1/analysis")
def list_analyses():
    return sorted(records.values(), key=lambda item: item["created_at"], reverse=True)

@app.delete("/api/v1/analysis/{analysis_id}")
def delete_analysis(analysis_id: str):
    get_analysis(analysis_id)
    records.pop(analysis_id, None)
    with _db() as db:
        db.execute("DELETE FROM analyses WHERE id=?", (analysis_id,))
    return {"deleted": True}

@app.post("/api/v1/analyze")
async def analyze_text(text: str = Form(default=""), mode: str = Form(default="offline"), filename: str = Form(default="Pasted contract"), file: UploadFile | None = File(default=None)):
    if file:
        try:
            data = await file.read(5 * 1024 * 1024 + 1)
            extracted, _ = extract_document(file.filename or "upload.txt", data)
            filename = file.filename or filename
            text = extracted
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
    if mode != "offline":
        raise HTTPException(501, "Live AI is not configured yet. Choose offline analysis or configure an LLM provider.")
    return create_analysis(text, filename, mode)

@app.get("/api/v1/analysis/{analysis_id}")
def get_analysis(analysis_id: str):
    if analysis_id not in records: raise HTTPException(404, "Analysis not found.")
    return records[analysis_id]

@app.get("/api/v1/analysis/{analysis_id}/clauses")
def get_clauses(analysis_id: str): return get_analysis(analysis_id)["clauses"]

@app.get("/api/v1/analysis/{analysis_id}/conflicts")
def get_conflicts(analysis_id: str): return get_analysis(analysis_id)["conflicts"]

@app.get("/api/v1/analysis/{analysis_id}/graph")
def get_graph(analysis_id: str):
    a = get_analysis(analysis_id)
    return {"nodes": [{"id": c["id"], "label": c["heading"], "risk_level": c["risk_level"]} for c in a["clauses"]], "edges": [{"id": x["id"], "source": x["clause_ids"][0], "target": x["clause_ids"][1], "type": x["conflict_type"], "severity": x["severity"]} for x in a["conflicts"]]}

@app.post("/api/v1/analysis/{analysis_id}/reviews")
def save_review(analysis_id: str, review: ReviewRequest):
    a = get_analysis(analysis_id)
    finding = next((f for f in a["findings"] if f["id"] == review.finding_id), None)
    if not finding: raise HTTPException(404, "Finding not found.")
    finding["review_status"] = review.decision
    a["reviews"].append({**review.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()})
    _persist(a)
    return finding

@app.post("/api/v1/analysis/{analysis_id}/rewrite")
def rewrite(analysis_id: str, payload: dict):
    a = get_analysis(analysis_id)
    cid = payload.get("clause_id")
    clause = next((c for c in a["clauses"] if c["id"] == cid), None)
    if not clause: raise HTTPException(404, "Clause not found.")
    return {"original": clause["text"], "suggestion": "Draft alternative unavailable in offline mode. Configure a live LLM provider to generate proposed wording.", "mode": "offline", "disclaimer": "Any proposed wording requires human review."}

@app.post("/api/v1/analysis/{analysis_id}/compare")
async def compare(analysis_id: str, file: UploadFile = File(...)):
    a = get_analysis(analysis_id)
    try: text, _ = extract_document(file.filename or "version.txt", await file.read(5 * 1024 * 1024 + 1))
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    import difflib
    return {"original_filename": a["filename"], "new_filename": file.filename, "diff": list(difflib.unified_diff(a["text"].splitlines(), text.splitlines(), fromfile="original", tofile="new")), "note": "Text-level comparison; changed provisions are not independently reanalyzed."}

@app.post("/api/v1/analysis/{analysis_id}/export")
def export_report(analysis_id: str):
    a = get_analysis(analysis_id)
    from io import BytesIO
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from fastapi.responses import Response
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=letter, rightMargin=.7*inch, leftMargin=.7*inch, topMargin=.7*inch, bottomMargin=.65*inch, title="CLAUSE-WISE Contract Review")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=31, textColor=colors.HexColor("#10213d"), alignment=TA_CENTER, spaceAfter=14))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], textColor=colors.HexColor("#1c4d89"), spaceBefore=14, spaceAfter=8))
    styles.add(ParagraphStyle(name="SmallBody", parent=styles["BodyText"], fontSize=9, leading=13, spaceAfter=5))
    styles.add(ParagraphStyle(name="Evidence", parent=styles["BodyText"], fontSize=9, leading=13, leftIndent=10, borderColor=colors.HexColor("#74a9f2"), borderWidth=1, borderPadding=7, backColor=colors.HexColor("#f0f5fc"), spaceBefore=4, spaceAfter=8))
    P = lambda value, style="SmallBody": Paragraph(escape(str(value)).replace("\n", "<br/>"), styles[style])
    story = [Spacer(1, 1.25*inch), P("CLAUSE-WISE", "SectionTitle"), P("Contract Review Report", "CoverTitle"), P(a["filename"]), Spacer(1, 12), P(f"Analysis date: {a['created_at'][:10]}"), P(f"Mode: {a['mode'].title()} · Clauses: {a['clause_count']} · Overall risk: {a['overall_score'] if a['overall_score'] is not None else 'Unavailable'} / 10"), Spacer(1, 20), P("REVIEW SUPPORT, NOT LEGAL ADVICE", "SectionTitle"), P("This report prioritizes contract provisions for human review. Scores are not probabilities of loss or measures of legal validity. Offline analysis uses deterministic rules and keyword matching; it may miss context-dependent risks and does not provide the same reasoning as live AI analysis."), PageBreak()]
    story.append(P("Executive summary", "SectionTitle"))
    story.append(P(f"{sum(c['risk_level']=='high' for c in a['clauses'])} high-risk clauses · {sum(c['risk_level']=='medium' for c in a['clauses'])} medium-risk clauses · {sum(c['risk_level']=='low' for c in a['clauses'])} low-risk clauses · {len(a['conflicts'])} potential conflict pairs"))
    story.append(P("Potential cross-clause conflicts", "SectionTitle"))
    if a["conflicts"]:
        for c in a["conflicts"]:
            story.append(KeepTogether([P(f"{c['title']} — {', '.join(c['clause_ids'])}"), P(c["explanation"]), P(f"Evidence — {c['clause_ids'][0]}: {c['evidence_a']}" , "Evidence"), P(f"Evidence — {c['clause_ids'][1]}: {c['evidence_b']}", "Evidence"), P(f"Reviewer action: {c['reviewer_action']}")]))
    else: story.append(P("No cross-clause conflicts were identified by the selected analysis mode."))
    story.append(P("Clause findings", "SectionTitle"))
    for c in a["clauses"]:
        fs = [f for f in a["findings"] if c["id"] in f["clause_ids"]]
        story.append(P(f"{c['id']} — {c['heading']} · Score: {c['risk_score'] if c['risk_score'] is not None else 'Unavailable'} / 10"))
        if fs:
            for f in fs:
                story.extend([P(f"{f['title']} · {f['agent_type']} · {f['score']}/10"), P(f["explanation"]), P(f"Evidence: {f['evidence']}", "Evidence"), P(f"Reviewer action: {f['reviewer_action']}")])
        else: story.append(P("No rule-based finding was returned for this clause."))
    story.extend([Spacer(1, 12), P("Reviewer notes", "SectionTitle"), P("Add review notes to your retained case record. This export does not contain notes unless they were entered into the analysis.")])
    doc.build(story)
    return Response(stream.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=clause-wise-report.pdf"})

