import jwt
import os
import base64

from passlib.context import CryptContext
from fastapi import HTTPException
from jwt import ExpiredSignatureError, InvalidSignatureError, InvalidTokenError

from utils import now


# public JSON Web Token signature key
PUBLIC_RSA_KEY = base64.b64decode(os.getenv('PUBLIC_RSA_KEY'))
# private JSON Web Token signature key
PRIVATE_RSA_KEY = base64.b64decode(os.getenv('PRIVATE_RSA_KEY'))


class PasswordManager:
    """The PasswordManager manages hashing and checking passwords."""

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


class TokenManager:
    """The TokenManager manages encoding and decoding JSON Web Tokens."""

    ACCESS_TOKEN_TTL = 30*60  # 30 minutes
    REFRESH_TOKEN_TTL = 7*24*60*60  # 7 days

    def generate(self, admin_id, time_to_live):
        """Generate a JWT containing the user id and an expiration date."""
        timestamp = now()
        payload = {
            'iss': 'FastSurvey',
            'sub': admin_id,
            'iat': timestamp,
            'exp': timestamp + time_to_live,
        }
        return jwt.encode(payload, PRIVATE_RSA_KEY, algorithm='RS256')

    def decode(self, token):
        """Decode the given JWT and return the user id."""
        try:
            payload = jwt.decode(token, PUBLIC_RSA_KEY, algorithm='RS256')
        except ExpiredSignatureError:
            raise HTTPException(401, 'token expired')
        except InvalidSignatureError:
            raise HTTPException(401, 'signature verification failed')
        except InvalidTokenError:
            raise HTTPException(400, 'invalid token format')
        return payload['sub']

    def oauth(self, admin_id):
        """Generate an OAuth2 token containing an access and refresh JWT."""
        return {
            'access_token': self.generate(admin_id, self.ACCESS_TOKEN_TTL),
            'refresh_token': self.generate(admin_id, self.REFRESH_TOKEN_TTL),
            'token_type': 'bearer',
        }
