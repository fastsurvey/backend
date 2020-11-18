import jwt
import os
import base64

from passlib.context import CryptContext
from fastapi import HTTPException
from datetime import datetime, timedelta
from jwt import ExpiredSignatureError, InvalidSignatureError, InvalidTokenError


class PasswordManager:
    """The PasswordManager manages hashing and checking passwords."""

    def __init__(self):
        """Initialize a password manager instance."""
        self.context = CryptContext(
            schemes=['argon2'],
            deprecated='auto',
        )

    def hash_password(self, password: str):
        """Hash the given password and return the hash as string."""
        return self.context.hash(password)

    def verify_password(self, password: str, pwdhash: str):
        """Return true if the password results in the hash, else False."""
        return self.context.verify(password, pwdhash)


class TokenManager:
    """The TokenManager manages encoding and decoding JSON Web Tokens."""

    PUBLIC_RSA_KEY = base64.b64decode(os.getenv('PUBLIC_RSA_KEY'))
    PRIVATE_RSA_KEY = base64.b64decode(os.getenv('PRIVATE_RSA_KEY'))
    ACCESS_TOKEN_TTL = 30*60  # 30 minutes
    REFRESH_TOKEN_TTL = 48*60*60  # 2 days

    def generate(self, user_id: str, ttl: int):
        """Generate a JWT containing the user id and an expiration date."""
        payload = {
            'iss': 'authentication-backend',
            'sub': user_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(ttl),
        }
        return jwt.encode(payload, self.PRIVATE_RSA_KEY, algorithm='RS256')

    def generate_access_token(self, user_id: str):
        """Generate an access token JWT containing the user id."""
        return self.generate(user_id, self.ACCESS_TOKEN_TTL)

    def generate_refresh_token(self, user_id: str):
        """Generate a refresh token JWT containing the user id."""
        return self.generate(user_id, self.REFRESH_TOKEN_TTL)

    def decode(self, token: str):
        """Decode the given JWT and return the user id."""
        try:
            payload = jwt.decode(token, self.PUBLIC_RSA_KEY, algorithm='RS256')
        except ExpiredSignatureError:
            raise HTTPException(401, 'token expired')
        except InvalidSignatureError:
            raise HTTPException(401, 'signature verification failed')
        except InvalidTokenError:
            raise HTTPException(400, 'invalid token format')
        return payload['uid']
