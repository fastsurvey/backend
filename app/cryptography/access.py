import jwt
import base64
import os
import fastapi
import functools

import app.utils as utils


# public JSON Web Token signature key
PUBLIC_RSA_KEY = base64.b64decode(os.getenv('PUBLIC_RSA_KEY'))
# private JSON Web Token signature key
PRIVATE_RSA_KEY = base64.b64decode(os.getenv('PRIVATE_RSA_KEY'))


def authorize(func):
    """Enforce proper authorization for the given function.

    A user is authorized if the username from the decrypted access token
    equals the given username. We handle every exception that can occur
    during the decoding process. If the decoding runs through without
    issues, we trust that the token is from us and skip further format
    verifications (e.g. if the token has all the required fields).

    """
    @functools.wraps(func)
    async def wrapper(username, access_token, *args):
        if username != decode(access_token):
            raise fastapi.HTTPException(401, 'invalid access token')
        await func(username, *args)
    return wrapper


def generate(username):
    """Generate JWT access token containing username and expiration.

    Note that the backend returns the access_token in the form
    {'access_token': 'tomato', 'token_type': 'bearer'} but expects only
    the actual 'tomato' value for any routes that require authorization.

    """
    timestamp = utils.now()
    payload = {
        'iss': 'FastSurvey',
        'sub': username,
        'iat': timestamp,
        'exp': timestamp + 7*24*60*60,  # tokens are valid for 7 days
    }
    access_token = jwt.encode(payload, PRIVATE_RSA_KEY, algorithm='RS256')
    return {'access_token': access_token, 'token_type': 'bearer'}


def decode(access_token):
    """Decode the given JWT access token and return the username."""
    try:
        payload = jwt.decode(access_token, PUBLIC_RSA_KEY, algorithms=['RS256'])
        return payload['sub']
    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidSignatureError,
        jwt.DecodeError,
        jwt.InvalidTokenError,
    ):
        raise fastapi.HTTPException(401, 'invalid access token')
