import passlib


CONTEXT = passlib.context.CryptContext(schemes=['argon2'], deprecated='auto')


def hash(self, password):
    """Hash the given password and return the hash as string."""
    return self.CONTEXT.hash(password)


def verify(self, password, pwdhash):
    """Return true if the password results in the hash, else False."""
    return self.CONTEXT.verify(password, pwdhash)
