import pytest
import copy

import app.main as main
import app.validation as validation


def test_generate_schema(configurations, schemas):
    """Test that the schema generation function returns the correct result."""
    for survey_name, configuration in configurations.items():
        schema = validation._generate_schema(configuration)
        assert schema == schemas[survey_name]


@pytest.fixture(scope='session')
def validator(configurations):
    """Provide validator for configuration-independent rule testing."""
    configuration = configurations['email']  # generic configuration
    return validation.SubmissionValidator.create(configuration)


def test_validate_min_chars_passing(validator):
    """Test that min_chars rule works correctly for some valid values."""
    assert validator._validate_min_chars(2, 'test', 'aa') is None
    assert validator._validate_min_chars(5, 'test', '       ') is None
    assert validator._validate_min_chars(0, 'test', '') is None


def test_validate_min_chars_failing(validator):
    """Test that min_chars rule works correctly for some invalid values."""
    with pytest.raises(AttributeError):
        validator._validate_min_chars(1, 'test', '')
    with pytest.raises(AttributeError):
        validator._validate_min_chars(1000000, 'test', 'hello!')
    with pytest.raises(AttributeError):
        validator._validate_min_chars(9, 'test', '12345678')


def test_validate_max_chars_passing(validator):
    """Test that max_chars rule works correctly for some valid values."""
    assert validator._validate_max_chars(2, 'test', 'aa') is None
    assert validator._validate_max_chars(100000, 'test', '   ') is None
    assert validator._validate_max_chars(0, 'test', '') is None


def test_validate_max_chars_failing(validator):
    """Test that max_chars rule works correctly for some invalid values."""
    with pytest.raises(AttributeError):
        validator._validate_max_chars(0, 'test', ' ')
    with pytest.raises(AttributeError):
        validator._validate_max_chars(9999, 'test', 'a' * 10000)
    with pytest.raises(AttributeError):
        validator._validate_max_chars(1, 'test', 'apple juice')


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
