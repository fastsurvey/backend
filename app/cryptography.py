import jwt
import os
import base64
import secrets

from passlib.context import CryptContext
from fastapi import HTTPException
from jwt import (
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError,
    InvalidTokenError,
)

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

    def hash(self, password):
        """Hash the given password and return the hash as string."""
        return self.context.hash(password)

    def verify(self, password, pwdhash):
        """Return true if the password results in the hash, else False."""
        return self.context.verify(password, pwdhash)

    def validate(self, password):
        """Validate that the password has the right format."""
        return 8 <= len(password) <= 64


class JWTManager:
    """The JWTManager manages encoding and decoding JSON Web Tokens."""

    # TODO would it be better to use the same private key for en-/decryption
    # here instead of a public/private keypair?

    def generate(self, username):
        """Generate JWT access token containing username and expiration.

        Note that the backend returns the access_token in the form
        {'access_token': 'tomato', 'token_type': 'bearer'} but expects only
        the actual 'tomato' value for any routes that require authorization.

        """
        timestamp = now()
        payload = {
            'iss': 'FastSurvey',
            'sub': username,
            'iat': timestamp,
            'exp': timestamp + 2*60*60,  # tokens are valid for 2 hours
        }
        access_token = jwt.encode(payload, PRIVATE_RSA_KEY, algorithm='RS256')
        return {'access_token': access_token, 'token_type': 'bearer'}

    def authorize(self, username, access_token):
        """Authorize user by comparing username with access token.

        We handle every exception that can occur during the decoding process.
        If the decoding runs through without issues, we trust that the
        token is from us and skip further format verifications (e.g. if the
        token has all the required fields).

        """
        try:
            assert username == self.decode(access_token)
        except (
            ExpiredSignatureError,
            InvalidSignatureError,
            DecodeError,
            InvalidTokenError,
            AssertionError,
        ):
            raise HTTPException(401, 'invalid access token')

    def decode(self, access_token):
        """Decode the given JWT access token and return the username."""
        payload = jwt.decode(
            access_token,
            PUBLIC_RSA_KEY,
            algorithms=['RS256'],
        )
        return payload['sub']


def vtoken():
    """Create and return a random hex string useful in verification flows."""
    return secrets.token_hex(64)
