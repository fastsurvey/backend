import passlib.context as context


_CONTEXT = context.CryptContext(schemes=['argon2'], deprecated='auto')


def hash(password):
    """Hash the given password and return the hash as string."""
    return _CONTEXT.hash(password)


def verify(password, password_hash):
    """Return true if the password results in the hash, else False."""
    return _CONTEXT.verify(password, password_hash)
