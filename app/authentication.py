import secrets
import passlib.context as context
import hashlib


_CONTEXT = context.CryptContext(schemes=['argon2'], deprecated='auto')


################################################################################
# Password Flow
################################################################################


def hash_password(password):
    """Hash the given password and return the hash as string."""
    return _CONTEXT.hash(password)


def verify_password(password, password_hash):
    """Return true if the password results in the hash, else False."""
    return _CONTEXT.verify(password, password_hash)


################################################################################
# Token Flow
################################################################################


def generate_token():
    """Create and return a random string useful for authentication."""
    return secrets.token_urlsafe(48)


def hash_token(token):
    """Hash the given token and return the hash as string."""
    return hashlib.sha512(token.encode('utf-8')).hexdigest()
