import re
from app.agents import clause_quality, liability, jurisdiction, contradiction

RULES = [
    ("liability", r"unlimited liability|without limitation|liability shall not be limited", "Potentially uncapped liability", 8, "Review the scope and any exceptions to the liability cap."),
    ("liability", r"liability cap|aggregate liability|shall not exceed", "Liability cap identified", 3, "Confirm the cap amount and which claims are excluded."),
    ("indemnity", r"indemnif(?:y|ies|ication)", "Indemnity obligation", 5, "Check scope, covered losses, process, and any cap carve-out."),
    ("renewal", r"automatically renew|auto.?renew", "Automatic renewal term", 5, "Confirm the renewal period and cancellation deadline."),
    ("termination", r"terminate|termination", "Termination provision", 2, "Confirm termination rights and notice requirements."),
    ("modification", r"sole discretion|unilaterally|may modify", "One-sided discretion or modification", 6, "Review whether notice, consent, or an exit right is appropriate."),
    ("jurisdiction", r"governing law|governed by the laws", "Governing law provision", 2, "Distinguish governing law from court venue and arbitration seat."),
    ("jurisdiction", r"arbitration|courts? of", "Dispute forum identified", 2, "Confirm forum, seat, venue, and procedure are mutually workable."),
    ("notice", r"(\d+)\)?\s+days?['’]?\s+(?:(?:prior|written)(?:\s+written)?\s+)?notice", "Notice period", 3, "Check notice period against other termination and renewal provisions."),
]


def analyze(clauses: list[dict]) -> tuple[list[dict], list[dict]]:
    findings = []
    for clause in clauses:
        low = clause["text"].lower()
        # Keep the specialist rule boundaries explicit even when offline mode uses regex checks.
        specialist_hits = {
            "clause_quality": clause_quality.inspect(clause),
            "liability": liability.inspect(clause),
            "jurisdiction": jurisdiction.inspect(clause),
        }
        for category, pattern, title, score, action in RULES:
            if re.search(pattern, low):
                agent_type = "liability" if category in ("liability", "indemnity") else "jurisdiction" if category == "jurisdiction" else "clause_quality"
                if not specialist_hits[agent_type]:
                    continue
                m = re.search(pattern, clause["text"], re.I)
                quote = clause["text"][max(0, m.start()-70):min(len(clause["text"]), m.end()+140)].strip()
                findings.append({"id": f"F-{len(findings)+1:03d}", "agent_type": agent_type, "clause_ids": [clause["id"]], "score": score, "category": category, "title": title, "explanation": f"Offline {agent_type.replace('_', ' ')} pattern check detected language related to {category}. Context and exceptions require human review.", "evidence": quote, "potential_impact": "The provision may affect obligations, exposure, or review timing depending on the full contract context.", "reviewer_action": action, "uncertainty": "Rule-based keyword match; not a legal conclusion and may miss context.", "validation_status": "valid", "review_status": "unreviewed"})
    return findings, contradiction.inspect(clauses)
