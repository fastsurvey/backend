import pytest
import jwt
import os
import base64

from fastapi import HTTPException

import app.main as main
import app.cryptography as cryptography


def test_password_hashing():
    """Test password hashing and verifying with diverse passwords."""
    passwords = ['hello', 'world', 'A'*1000, '', 'Ӂ', 'ٸ', '៼']
    password_manager = main.account_manager.password_manager
    for password in passwords:
        password_hash = password_manager.hash_password(password)
        assert password_manager.verify_password(password, password_hash)


def test_valid_access_token_procedure(test_parameters):
    """Test JWT access token generation and decoding procedure."""
    username = test_parameters['username']
    access_token = main.token_manager.generate(username)
    assert main.token_manager.authorize(username, access_token) is None


def test_invalid_access_token_procedure(username, private_rsa_key):
    """Test that JWT decoding fails for some example invalid tokens."""
    with pytest.raises(HTTPException, match='unauthorized'):
        access_token = main.token_manager.generate('orange')
        main.token_manager.authorize(username, access_token)
    with pytest.raises(HTTPException, match='invalid token format'):
        access_token = 'hello world'
        main.token_manager.authorize(username, access_token)
    with pytest.raises(HTTPException, match='invalid token format'):
        access_token = None
        main.token_manager.authorize(username, access_token)
    with pytest.raises(HTTPException, match='invalid token format'):
        access_token = {'access_token': 'abc', 'token_type': 'bearer'}
        main.token_manager.authorize(username, access_token)
    with pytest.raises(HTTPException, match='token expired'):
        access_token = {
            'access_token': jwt.encode(
                {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 0},
                key=cryptography.PRIVATE_RSA_KEY,
                algorithm='RS256',
            ),
            'token_type': 'bearer',
        }
        main.token_manager.authorize(username, access_token)
    with pytest.raises(HTTPException, match='signature verification failed'):
        access_token = {
            'access_token': jwt.encode(
                {'iss': 'FastSurvey', 'sub': username, 'iat': 0, 'exp': 0},
                key=base64.b64decode(private_rsa_key),
                algorithm='RS256',
            ),
            'token_type': 'bearer',
        }
        main.token_manager.authorize(username, access_token)

