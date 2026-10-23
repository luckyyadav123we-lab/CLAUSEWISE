"""Clause quality rules for the deterministic offline mode."""
PATTERNS = [r"sole discretion", r"unilaterally", r"may modify", r"automatically renew", r"terminate", r"\d+\)?\s+days?.{0,24}notice"]

def inspect(clause: dict) -> list[str]:
    import re
    return [pattern for pattern in PATTERNS if re.search(pattern, clause["text"], re.I)]
