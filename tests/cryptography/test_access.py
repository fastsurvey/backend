import pytest
import jwt
import os
import base64
import fastapi

import app.cryptography.access as access


# private JSON Web Token signature key
PRIVATE_RSA_KEY = base64.b64decode(os.getenv('PRIVATE_RSA_KEY'))


def test_valid_access_token_procedure(username):
    """Test JWT access token generation and decoding procedure."""
    access_token = access.generate(username)['access_token']
    assert access.decode(access_token) == username


@pytest.mark.asyncio
async def test_invalid_access_token_procedure(username, variables):
    """Test that JWT decoding fails for some example invalid tokens."""
    access_tokens = [
        42,
        3.14,
        None,
        '',
        'password',
        [],
        {},
        access.generate(username)['access_token'][:-1],
        access.generate(username.upper())['access_token'],
        access.generate(f'{username}+')['access_token'],
        jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 0},
            key=PRIVATE_RSA_KEY,
            algorithm='RS256',
        ),
        jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 4102444800},
            key=base64.b64decode(variables['wrong_private_rsa_key']),
            algorithm='RS256',
        ),
        jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 4102444800},
            key=PRIVATE_RSA_KEY,
            algorithm='HS256',
        ),
        jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 4102444800},
            key=PRIVATE_RSA_KEY,
            algorithm='RS512',
        ),
    ]
    for access_token in access_tokens:
        with pytest.raises(fastapi.HTTPException):
            await access.authorize(lambda x : None)(username, access_token)
