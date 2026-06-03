# Utils package initialization file
import re

PHONE_RE = re.compile(r'^[0-9 +]*$')
PHONE_ERROR = 'Only digits (0–9), spaces, and + are allowed.'


def is_valid_phone(value):
    """Return True if value is empty or contains only digits, spaces, and +."""
    if not value:
        return True
    return bool(PHONE_RE.match(value))