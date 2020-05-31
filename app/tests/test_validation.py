import pytest
import os
import json

from .. import validation


@pytest.fixture
def template(scope='module'):
    folder = os.path.join(os.path.dirname(__file__), '../surveys')
    with open(os.path.join(folder, 'test-survey.json'), 'r') as template:
        return json.load(template)


@pytest.fixture
def validator(template, scope='module'):
    return validation.create_validator(template)


def test_generate_schema(template):
    """Test that the schema generation function returns the correct result."""
    schema = validation._generate_schema(template)
    assert schema ==  {
        'email': {
            'type': 'string',
            'regex': r'^[a-z]{2}[0-9]{2}[a-z]{3}@mytum\.de$',
        },
        'properties': {
            'type': 'dict',
            'schema': {
                'election': {
                    'type': 'Selection',
                    'min_select': 0,
                    'max_select': 2,
                    'schema': {
                        'felix': {
                            'type': 'Option',
                        },
                        'moritz': {
                            'type': 'Option',
                        },
                        'andere': {
                            'type': 'List',
                        },
                    },
                },
                'reason': {
                    'type': 'Text',
                    'min_chars': 10,
                    'max_chars': 100,
                }
            },
        },
    }


submission = {
    'email': 'tt00est@mytum.de',
    'properties': {
        'election': {
            'felix': True,
            'moritz': True,
            'andere': '',
        },
        'reason': 'hello world!',
    }
}


def test_validator_passing(validator):
    """Check that the generated validator lets a valid submissions pass."""
    assert validator.validate(submission)


def test_email_passing(validator):
    """Check that the validator lets some valid email addresses pass."""
    emails = [
        'tt00est@mytum.de',
        'ia72ihd@mytum.de',
    ]
    sub = submission.copy()
    for email in emails:
        sub['email'] = email
        assert validator.validate(sub)


def test_email_failing(validator):
    """Check that the validator rejects some invalid email addresses."""
    emails = [
        8,
        None,
        {},
        True,
        '',
        'sadfj',
        'FFFFFFF@mytum.de',
        'tt00est@mytum.de ',
        'a123adf@mytum.de',
        'ab82eee@mytum8de',
        'a12 93ad@mytum.de',
        'a123   @mytum.de',
        'a444+00@mytum.de',
        'tt00est@gmail.com',
        '123@mytum.de@mytum.de',
        'tt00est@mytum:de',
        'tT00est@mytum.de',
        'tt00eSt@mytum.de',
    ]
    sub = submission.copy()
    for email in emails:
        sub['email'] = email
        assert not validator.validate(sub)


def test_validate_min_chars_passing(validator):
    """Test that min_chars rule works correctly for some valid values."""
    assert validator._validate_min_chars(2, 'test', 'aa') is None
    assert validator._validate_min_chars(5, 'test', '             ') is None
    assert validator._validate_min_chars(0, 'test', '') is None


def test_validate_min_chars_failing(validator):
    """Test that min_chars rule works correctly for some invalid values."""
    with pytest.raises(AttributeError):
        validator._validate_min_chars(1, 'test', '')
    with pytest.raises(AttributeError):
        validator._validate_min_chars(1000000, 'test', 'hello!')


def test_validate_max_chars_passing(validator):
    """Test that max_chars rule works correctly for some valid values."""
    assert validator._validate_max_chars(2, 'test', 'aa') is None
    assert validator._validate_max_chars(100000, 'test', '          ') is None
    assert validator._validate_max_chars(0, 'test', '') is None


def test_validate_max_chars_failing(validator):
    """Test that max_chars rule works correctly for some invalid values."""
    with pytest.raises(AttributeError):
        validator._validate_max_chars(0, 'test', ' ')
    with pytest.raises(AttributeError):
        validator._validate_max_chars(9999, 'test', 'aaaaaaaaaa' * 1000)
