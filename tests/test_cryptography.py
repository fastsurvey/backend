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


def test_valid_access_token_procedure(test_parameters):
    """Test JWT access token generation and decoding procedure."""
    username = test_parameters['username']
    access_token = main.jwt_manager.generate(username)['access_token']
    assert main.jwt_manager.authorize(username, access_token) is None


def test_invalid_access_token_procedure(username, private_rsa_key):
    """Test that JWT decoding fails for some example invalid tokens."""
    with pytest.raises(HTTPException, match='invalid access token'):
        access_token = main.jwt_manager.generate('orange')['access_token']
        main.jwt_manager.authorize(username, access_token)
    with pytest.raises(HTTPException, match='invalid access token'):
        main.jwt_manager.decode(42)
    with pytest.raises(HTTPException, match='invalid access token'):
        main.jwt_manager.decode(None)
    with pytest.raises(HTTPException, match='invalid access token'):
        access_token = main.jwt_manager.generate(username)['access_token'][:-1]
        main.jwt_manager.decode(access_token)
    with pytest.raises(HTTPException, match='invalid access token'):
        access_token = jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 0},
            key=cryptography.PRIVATE_RSA_KEY,
            algorithm='RS256',
        )
        main.jwt_manager.decode(access_token)
    with pytest.raises(HTTPException, match='invalid access token'):
        access_token = jwt.encode(
            {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 0},
            key=base64.b64decode(private_rsa_key),
            algorithm='RS256',
        )
        main.jwt_manager.decode(access_token)
