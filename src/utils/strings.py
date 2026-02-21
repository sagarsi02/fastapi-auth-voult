"""String normalization helpers used across routes/services."""


def normalize_email(email: str) -> str:
    """Return normalized email for consistent lookup and storage."""
    return email.strip().lower()
