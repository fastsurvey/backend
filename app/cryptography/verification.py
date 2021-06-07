import secrets


def token():
    """Create and return a random string useful for verification flows."""
    return secrets.token_urlsafe(48)
