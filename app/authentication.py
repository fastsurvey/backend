import secrets
import passlib.context as context
import hashlib
import functools

import app.resources.database as database
import app.utils as utils
import app.errors as errors


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


def authorize(func):
    """Enforce proper authorization for the given fastapi route."""
    @functools.wraps(func)
    async def wrapper(**kwargs):
        res = await database.database['access_tokens'].update_one(
            filter={'access_token': hash_token(kwargs['data'].access_token)},
            update={'$set': {'issuance_time': utils.now()}}
        )
        if res.matched_count == 0:
            raise errors.AccessForbiddenError()
        return await func(**kwargs)
    return wrapper
