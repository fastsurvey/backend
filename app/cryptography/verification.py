import secrets


def token():
    """Create and return a random hex string useful in verification flows."""
    return secrets.token_hex(64)
