"""Governing law and dispute resolution rule checks."""
PATTERNS = [r"governing law", r"governed by the laws", r"arbitration", r"courts? of"]

def inspect(clause: dict) -> list[str]:
    import re
    return [pattern for pattern in PATTERNS if re.search(pattern, clause["text"], re.I)]
