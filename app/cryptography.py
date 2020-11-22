import jwt
import os
import base64

from passlib.context import CryptContext
from fastapi import HTTPException
from jwt import ExpiredSignatureError, InvalidSignatureError, InvalidTokenError

from app.utils import now


# public JSON Web Token signature key
PUBLIC_RSA_KEY = base64.b64decode(os.getenv('PUBLIC_RSA_KEY'))
# private JSON Web Token signature key
PRIVATE_RSA_KEY = base64.b64decode(os.getenv('PRIVATE_RSA_KEY'))


class PasswordManager:
    """The PasswordManager hashes, verifies and validates passwords."""

    def __init__(self):
        """Initialize a password manager instance."""
        self.context = CryptContext(
            schemes=['argon2'],
            deprecated='auto',
        )

    def hash_password(self, password):
        """Hash the given password and return the hash as string."""
        return self.context.hash(password)

    def verify_password(self, password, pwdhash):
        """Return true if the password results in the hash, else False."""
        return self.context.verify(password, pwdhash)

    def validate_password(self, password):
        """Validate that the password has the right format."""
        return 8 <= len(password) <= 64


class TokenManager:
    """The TokenManager manages encoding and decoding JSON Web Tokens."""

    def generate(self, admin_id):
        """Generate a JWT access token containing user id and expiration."""
        timestamp = now()
        payload = {
            'iss': 'FastSurvey',
            'sub': admin_id,
            'iat': timestamp,
            'exp': timestamp + 2*60*60,  # tokens are valid for 2 hours
        }
        access_token = jwt.encode(payload, PRIVATE_RSA_KEY, algorithm='RS256')
        return {'access_token': access_token, 'token_type': 'bearer'}

    def decode(self, token):
        """Decode the given JWT access token and return the user id."""
        try:
            payload = jwt.decode(token, PUBLIC_RSA_KEY, algorithm='RS256')
        except ExpiredSignatureError:
            raise HTTPException(401, 'token expired')
        except InvalidSignatureError:
            raise HTTPException(401, 'signature verification failed')
        except InvalidTokenError:
            raise HTTPException(400, 'invalid token format')
        return payload['sub']
