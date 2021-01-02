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


def test_valid_access_token_procedure(admin_name):
    """Test JWT access token generation and decoding procedure."""
    access_token = main.token_manager.generate(admin_name)
    assert main.token_manager.authorize(admin_name, access_token) is None


def test_invalid_access_token_procedure(admin_name):
    """Test that JWT decoding fails for some example invalid tokens."""

    # TODO test correct denial when generated with other secret

    with pytest.raises(HTTPException, match='unauthorized'):
        access_token = main.token_manager.generate('orange')
        main.token_manager.authorize(admin_name, access_token)
    with pytest.raises(HTTPException, match='invalid token format'):
        access_token = 'hello world'
        main.token_manager.authorize(admin_name, access_token)
    with pytest.raises(HTTPException, match='invalid token format'):
        access_token = None
        main.token_manager.authorize(admin_name, access_token)
    with pytest.raises(HTTPException, match='invalid token format'):
        access_token = {'access_token': 'abc', 'token_type': 'bearer'}
        main.token_manager.authorize(admin_name, access_token)
    with pytest.raises(HTTPException, match='token expired'):
        access_token = {
            'access_token': jwt.encode(
                {
                    'iss': 'FastSurvey',
                    'sub': admin_name,
                    'iat': 0,
                    'exp': 0,
                },
                key=cryptography.PRIVATE_RSA_KEY,
                algorithm='RS256',
            ),
            'token_type': 'bearer',
        }
        main.token_manager.authorize(admin_name, access_token)
