import re

def normalize_id(raw: str) -> str:
    s = raw.strip().upper().replace("_", "-").replace(" ", "")
    s = re.sub(r"[^A-Z0-9-]", "", s)

    if s.startswith(("S-", "L-")):
        return s

    if s.isdigit():
        return f"S-{s}"

    return s
