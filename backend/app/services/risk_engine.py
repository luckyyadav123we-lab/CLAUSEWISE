from collections import defaultdict


def level(score: int | None) -> str:
    if score is None:
        return "unavailable"
    return "low" if score <= 3 else "medium" if score <= 6 else "high"


def score_clauses(clauses: list[dict], findings: list[dict]) -> list[dict]:
    by_clause: dict[str, list[dict]] = defaultdict(list)
    for finding in findings:
        if finding.get("validation_status") == "valid" and isinstance(finding.get("score"), int) and 0 <= finding["score"] <= 10:
            for cid in finding.get("clause_ids", []):
                by_clause[cid].append(finding)
    result = []
    for clause in clauses:
        items = by_clause.get(clause["id"], [])
        scores = [f["score"] for f in items]
        if not scores:
            result.append({**clause, "risk_score": None, "risk_level": "unavailable", "primary_agent": None, "corroborating_agents": []})
            continue
        best = max(scores)
        primary = next(f["agent_type"] for f in items if f["score"] == best)
        corroborating = list(dict.fromkeys(f["agent_type"] for f in items if f["agent_type"] != primary and f["score"] >= 5))
        final = min(10, best + bool(corroborating))
        result.append({**clause, "risk_score": final, "risk_level": level(final), "primary_agent": primary, "corroborating_agents": corroborating})
    return result
