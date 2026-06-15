from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    # Credit card (16 digits with optional separators) — must run before cccd/phone
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    # CCCD: exactly 12 consecutive digits, no digit neighbours
    "cccd": r"(?<!\d)\d{12}(?!\d)",
    # VN phone: local (0xx...) or international (+84 xx...) format
    # Covers: 0987654321, 090 123 4567, 090.123.4567, +84 987 654 321, +84-987-654-321
    # Strategy: match prefix then 8-9 remaining digits with optional separators between each digit group
    "phone_vn": r"(?:\+84|0)(?:[\s\.\-]?\d){8,10}(?!\d)",
    # VN passport: one uppercase letter followed by 7 or 8 digits
    "passport": r"\b[A-Z]\d{7,8}\b",
    # VN address keywords
    "address_vn": r"(?:số\s+\d+[,\s]+)?(?:đường|phố|ngõ|ngách)\s+[\w\s]+,?\s*(?:phường|xã)\s+[\w\s]+,?\s*(?:quận|huyện|thị\s+xã)\s+[\w\s]+",
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
