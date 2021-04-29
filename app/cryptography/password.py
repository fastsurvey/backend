import passlib.context as context


CONTEXT = context.CryptContext(schemes=['argon2'], deprecated='auto')


def hash(password):
    """Hash the given password and return the hash as string."""
    return CONTEXT.hash(password)


def verify(password, pwdhash):
    """Return true if the password results in the hash, else False."""
    return CONTEXT.verify(password, pwdhash)
