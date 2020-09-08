import pytest
import copy

import app.main as main
import app.validation as validation


@pytest.mark.skip(reason='scheduled for refactoring')
def test_generate_schema(survey):
    """Test that the schema generation function returns the correct result."""
    schema = validation._generate_schema(survey.cn)
    assert schema ==  {
        'email': {
            'type': 'Email',
            'regex': r'^[a-z]{2}[0-9]{2}[a-z]{3}@mytum\.de$',
        },
        'properties': {
            'type': 'Properties',
            'schema': {
                '1': {
                    'type': 'Radio',
                    'schema': {
                        '1': {'type': 'Option'},
                        '2': {'type': 'Option'},
                    },
                },
                '2': {
                    'type': 'Selection',
                    'min_select': 0,
                    'max_select': 2,
                    'schema': {
                        '1': {'type': 'Option'},
                        '2': {'type': 'Option'},
                        '3': {'type': 'Option'},
                    },
                },
                '3': {
                    'type': 'Text',
                    'min_chars': 10,
                    'max_chars': 100,
                }
            },
        },
    }


@pytest.mark.skip(reason='scheduled for refactoring')
def test_validate_min_chars_passing(survey):
    """Test that min_chars rule works correctly for some valid values."""
    assert survey.validator._validate_min_chars(2, 'test', 'aa') is None
    assert survey.validator._validate_min_chars(5, 'test', '       ') is None
    assert survey.validator._validate_min_chars(0, 'test', '') is None


@pytest.mark.skip(reason='scheduled for refactoring')
def test_validate_min_chars_failing(survey):
    """Test that min_chars rule works correctly for some invalid values."""
    with pytest.raises(AttributeError):
        survey.validator._validate_min_chars(1, 'test', '')
    with pytest.raises(AttributeError):
        survey.validator._validate_min_chars(1000000, 'test', 'hello!')


@pytest.mark.skip(reason='scheduled for refactoring')
def test_validate_max_chars_passing(survey):
    """Test that max_chars rule works correctly for some valid values."""
    assert survey.validator._validate_max_chars(2, 'test', 'aa') is None
    assert survey.validator._validate_max_chars(100000, 'test', '   ') is None
    assert survey.validator._validate_max_chars(0, 'test', '') is None


@pytest.mark.skip(reason='scheduled for refactoring')
def test_validate_max_chars_failing(survey):
    """Test that max_chars rule works correctly for some invalid values."""
    with pytest.raises(AttributeError):
        survey.validator._validate_max_chars(0, 'test', ' ')
    with pytest.raises(AttributeError):
        survey.validator._validate_max_chars(9999, 'test', 'a' * 10000)


@pytest.fixture(scope='module')
def selection():
    """Provide a correct sample selection field for the test survey."""
    return {
        '1': False,
        '2': True,
        '3': True,
        '4': False,
        '5': True,
    }


@pytest.mark.skip(reason='scheduled for refactoring')
def test_validate_min_select_passing(survey, selection):
    """Test that min_select rule works correctly for some valid values."""
    assert survey.validator._validate_min_select(3, 'test', selection) is None
    assert survey.validator._validate_min_select(0, 'test', selection) is None


@pytest.mark.skip(reason='scheduled for refactoring')
def test_validate_min_select_failing(survey, selection):
    """Test that min_select rule works correctly for some invalid values."""
    with pytest.raises(AttributeError):
        survey.validator._validate_min_select(4, 'test', selection)
    with pytest.raises(AttributeError):
        survey.validator._validate_min_select(99999, 'test', selection)


@pytest.mark.skip(reason='scheduled for refactoring')
def test_validate_max_select_passing(survey, selection):
    """Test that max_select rule works correctly for some valid values."""
    assert survey.validator._validate_max_select(3, 'test', selection) is None
    assert survey.validator._validate_max_select(99, 'test', selection) is None


@pytest.mark.skip(reason='scheduled for refactoring')
def test_validate_max_select_failing(survey, selection):
    """Test that max_select rule works correctly for some invalid values."""
    with pytest.raises(AttributeError):
        survey.validator._validate_max_select(2, 'test', selection)
    with pytest.raises(AttributeError):
        survey.validator._validate_max_select(0, 'test', selection)


@pytest.mark.skip(reason='scheduled for refactoring')
def test_validator_passing(survey, submission):
    """Check that the generated validator lets a valid submissions pass."""
    assert survey.validator.validate(submission)


@pytest.mark.skip(reason='scheduled for refactoring')
def test_email_passing(survey, submission):
    """Check that the validator lets some valid email addresses pass."""
    emails = [
        'aa00aaa@mytum.de',
        'ia72ihd@mytum.de',
    ]
    submission = copy.deepcopy(submission)
    for email in emails:
        submission['email'] = email
        assert survey.validator.validate(submission)


@pytest.mark.skip(reason='scheduled for refactoring')
def test_email_failing(survey, submission):
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
    submission = copy.deepcopy(submission)
    for email in emails:
        submission['email'] = email
        assert not survey.validator.validate(submission)
