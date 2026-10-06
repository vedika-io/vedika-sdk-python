"""Which API operations accept an idempotency key.

Only the operations below list ``Idempotency-Key`` or ``X-Idempotency-Key`` in
the live OpenAPI document. Every other billed operation answers
``422 IDEMPOTENCY_NOT_SUPPORTED`` when a request carries a key, and treats a
caller-sent ``X-Request-Id`` as a key claim too. So the client attaches a key
automatically only to the operations listed here, and only when the caller did
not supply one. For every other operation a key is sent only when the caller
passes ``idempotency_key=``.

Each entry is ``(method, path template, header name)``. ``{name}`` matches one
path segment.
"""

import re
from typing import Optional

_CERTIFIED = (
    ("POST", "/api/v1/astrology/query", "X-Idempotency-Key"),
    ("POST", "/api/v1/vastu/chat/uploads", "Idempotency-Key"),
    ("POST", "/api/voice/binary", "Idempotency-Key"),
    ("POST", "/api/voice/stream", "Idempotency-Key"),
    ("POST", "/v2/astrology/karana", "X-Idempotency-Key"),
    ("POST", "/v2/astrology/nakshatra", "X-Idempotency-Key"),
    ("POST", "/v2/astrology/numerology/address", "Idempotency-Key"),
    ("POST", "/v2/astrology/numerology/balance", "Idempotency-Key"),
    ("POST", "/v2/astrology/numerology/birthday", "Idempotency-Key"),
    ("POST", "/v2/astrology/numerology/business-name", "Idempotency-Key"),
    ("POST", "/v2/astrology/numerology/chaldean/life-path", "Idempotency-Key"),
    ("POST", "/v2/astrology/numerology/pinnacle", "X-Idempotency-Key"),
    ("POST", "/v2/astrology/numerology/soul-urge", "X-Idempotency-Key"),
    ("POST", "/v2/astrology/numerology/vedic/sankhya", "X-Idempotency-Key"),
    ("POST", "/v2/astrology/tithi", "X-Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/archive/delete", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/archive/export", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/archive/summary", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/archive/tier", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/assessments/batch", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/audit/floor-plan", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/feed/listings", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/jobs", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/activity/export", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/activity/list", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/collaboration/comment", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/collaboration/get", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/collaboration/invite", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/collaboration/members", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/collaboration/review", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/collaboration/revoke", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/collaboration/update", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/create", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/delete", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/get", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/link-scan", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/list", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/properties/update", "Idempotency-Key"),
    ("POST", "/v2/astrology/vastu/quote/calculate", "Idempotency-Key"),
    ("POST", "/v2/astrology/yoga", "X-Idempotency-Key"),
    ("GET", "/v2/calculators/flames/{name1}/{name2}", "X-Idempotency-Key"),
    ("GET", "/v2/calculators/love-score/{name1}/{name2}", "X-Idempotency-Key"),
    ("GET", "/v2/lifestyle/love-compatibility/{sign1}/{sign2}", "Idempotency-Key"),
    ("GET", "/v2/lifestyle/lucky-color-today/{sign}", "Idempotency-Key"),
    ("GET", "/v2/lifestyle/spirit-animal/{sign}", "Idempotency-Key"),
    ("GET", "/v2/lifestyle/zodiac-fitness/{sign}", "Idempotency-Key"),
    ("GET", "/v2/lifestyle/zodiac-food/{sign}", "Idempotency-Key"),
    ("GET", "/v2/lifestyle/zodiac-gift/{sign}", "Idempotency-Key"),
    ("GET", "/v2/lifestyle/zodiac-travel/{sign}", "Idempotency-Key"),
    ("POST", "/v2/reports/prebuilt/generate", "Idempotency-Key"),
    ("POST", "/v2/vastu/archive/delete", "Idempotency-Key"),
    ("POST", "/v2/vastu/archive/export", "Idempotency-Key"),
    ("POST", "/v2/vastu/archive/summary", "Idempotency-Key"),
    ("POST", "/v2/vastu/archive/tier", "Idempotency-Key"),
    ("POST", "/v2/vastu/assessments/batch", "Idempotency-Key"),
    ("POST", "/v2/vastu/audit/floor-plan", "Idempotency-Key"),
    ("POST", "/v2/vastu/feed/listings", "Idempotency-Key"),
    ("POST", "/v2/vastu/jobs", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/activity/export", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/activity/list", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/collaboration/comment", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/collaboration/get", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/collaboration/invite", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/collaboration/members", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/collaboration/review", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/collaboration/revoke", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/collaboration/update", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/create", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/delete", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/get", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/link-scan", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/list", "Idempotency-Key"),
    ("POST", "/v2/vastu/properties/update", "Idempotency-Key"),
    ("POST", "/v2/vastu/quote/calculate", "Idempotency-Key"),
)


def _compile(template: str) -> "re.Pattern[str]":
    return re.compile("^" + re.sub(r"\\\{[^}/]+\\\}", "[^/]+", re.escape(template)) + "$")


_PATTERNS = tuple((method, _compile(path), header) for method, path, header in _CERTIFIED)


def certified_header(method: str, path: str) -> Optional[str]:
    """Header name to carry the key for a certified operation, else ``None``."""
    method = method.upper()
    path = path.split("?", 1)[0]
    for candidate_method, pattern, header in _PATTERNS:
        if candidate_method == method and pattern.match(path):
            return header
    return None
