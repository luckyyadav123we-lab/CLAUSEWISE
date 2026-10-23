from app.services.risk_engine import score_clauses, level
from app.services.document_parser import extract_document, segment
from fastapi.testclient import TestClient
from app.main import app

def test_scoring_corroboration_and_cap():
    clauses = [{"id": "CLAUSE-001", "heading": "x", "text": "x"}]
    findings = [{"clause_ids": ["CLAUSE-001"], "score": 10, "agent_type": "a", "validation_status": "valid"}, {"clause_ids": ["CLAUSE-001"], "score": 8, "agent_type": "b", "validation_status": "valid"}]
    assert score_clauses(clauses, findings)[0]["risk_score"] == 10
    assert score_clauses(clauses, findings)[0]["corroborating_agents"] == ["b"]

def test_no_scores_unavailable_and_levels():
    assert score_clauses([{"id":"x"}], [])[0]["risk_score"] is None
    assert [level(x) for x in [3,4,7,None]] == ["low","medium","high","unavailable"]

def test_txt_and_segmentation():
    text, _ = extract_document("terms.txt", b"1. Term\nFirst term\n2. Payment\nNet 30.")
    assert len(segment(text)) == 2

def test_reject_empty_and_unsupported():
    for name, data in [("a.txt", b""), ("a.pdf", b"not pdf"), ("a.exe", b"x")]:
        try: extract_document(name, data)
        except ValueError: pass
        else: assert False

def test_api_finds_evidence_linked_notice_conflict():
    client = TestClient(app)
    response = client.post("/api/v1/analyze", data={"text": "1. Termination\nEither party may terminate on thirty (30) days' prior written notice.\n\n2. Renewal\n90 days' written notice is required to avoid renewal."})
    assert response.status_code == 200
    result = response.json()
    assert len(result["conflicts"]) == 1
    conflict = result["conflicts"][0]
    assert conflict["clause_ids"] == ["CLAUSE-001", "CLAUSE-002"]
    assert "30) days" in conflict["evidence_a"]
    assert "90 days" in conflict["evidence_b"]
    report = client.post(f"/api/v1/analysis/{result['id']}/export")
    assert report.status_code == 200
    assert report.headers["content-type"] == "application/pdf"
    assert report.content.startswith(b"%PDF")
