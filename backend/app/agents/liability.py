"""Liability and financial exposure rule checks."""
PATTERNS = [r"unlimited liability", r"without limitation", r"liability cap", r"indemnif(?:y|ies|ication)"]

def inspect(clause: dict) -> list[str]:
    import re
    return [pattern for pattern in PATTERNS if re.search(pattern, clause["text"], re.I)]
