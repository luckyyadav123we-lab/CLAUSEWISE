"""Whole-contract comparison of notice periods across clauses."""
import re

NOTICE = re.compile(r"(\d+)\)?\s+days?['’]?\s+(?:(?:prior|written)(?:\s+written)?\s+)?notice", re.I)

def inspect(clauses: list[dict]) -> list[dict]:
    notice = []
    for clause in clauses:
        for match in NOTICE.finditer(clause["text"]):
            evidence = clause["text"][max(0, match.start()-55):min(len(clause["text"]), match.end()+80)].strip()
            notice.append((clause, int(match.group(1)), evidence))
    conflicts = []
    for i, (a, days_a, evidence_a) in enumerate(notice):
        for b, days_b, evidence_b in notice[i+1:]:
            if a["id"] == b["id"] or days_a == days_b:
                continue
            conflicts.append({"id": f"X-{len(conflicts)+1:03d}", "agent_type": "contradiction", "clause_ids": [a["id"], b["id"]], "conflict_type": "notice_period", "severity": "high" if abs(days_a-days_b) >= 60 else "medium", "title": f"Different notice periods: {days_a} and {days_b} days", "explanation": "Two clauses state different notice periods. The provisions may apply to different events, so compare their scope and any priority language.", "evidence_a": evidence_a, "evidence_b": evidence_b, "relationship": "conditionally_inconsistent", "potential_consequence": "A party may be unsure which notice deadline controls.", "reviewer_action": "Clarify which notice period applies to each event and align cross-references.", "uncertainty": "Offline comparison cannot determine whether the periods govern different events.", "review_status": "unreviewed"})
    return conflicts
