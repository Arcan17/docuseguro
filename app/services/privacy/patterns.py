import re

# Chilean RUT: 12.345.678-9 or 12345678-9 or 12345678-K
RUT_RE = re.compile(
    r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b",
    re.IGNORECASE,
)

# Standard email addresses
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
)

# Chilean mobile / landline: +56 9 XXXX XXXX or +569XXXXXXXX or 09XXXXXXXX
PHONE_CL_RE = re.compile(
    r"(?:\+56\s?9?\s?\d{4}\s?\d{4}|\b09\d{8}\b|\b9\d{8}\b)",
)

PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (RUT_RE, "rut"),
    (EMAIL_RE, "email"),
    (PHONE_CL_RE, "phone"),
]
