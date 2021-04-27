import pytest
import jwt
import os
import base64

from fastapi import HTTPException
from jwt import (
    ExpiredSignatureError,
    InvalidSignatureError,
    DecodeError,
    InvalidTokenError,
)

import app.main as main
import app.cryptography as cryptography


def test_password_hashing():
    """Test password hashing and verifying with diverse passwords."""
    passwords = ['hello', 'world', 'A'*1000, '', 'Ӂ', 'ٸ', '៼']
    password_manager = main.account_manager.password_manager
    for password in passwords:
        password_hash = password_manager.hash(password)
        assert password_manager.verify(password, password_hash)


def test_valid_access_token_procedure(username):
    """Test JWT access token generation and decoding procedure."""
    access_token = main.jwt_manager.generate(username)['access_token']
    assert main.jwt_manager.authorize(username, access_token) is None


def test_invalid_access_token_procedure(username, variables):
    """Test that JWT decoding fails for some example invalid tokens."""
    access_tokens = [
        42,
        3.14,
        None,
        '',
        'password',
        [],
        {},
        main.jwt_manager.generate(username)['access_token'][:-1],
        main.jwt_manager.generate(username.upper())['access_token'],
        main.jwt_manager.generate(f'{username}+')['access_token'],
        jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 0},
            key=cryptography.PRIVATE_RSA_KEY,
            algorithm='RS256',
        ),
        jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 4102444800},
            key=base64.b64decode(variables['wrong_private_rsa_key']),
            algorithm='RS256',
        ),
        jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 4102444800},
            key=cryptography.PRIVATE_RSA_KEY,
            algorithm='HS256',
        ),
        jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 4102444800},
            key=cryptography.PRIVATE_RSA_KEY,
            algorithm='RS512',
        ),
    ]
    for access_token in access_tokens:
        with pytest.raises(HTTPException, match='invalid access token'):
            main.jwt_manager.authorize(username, access_token)
