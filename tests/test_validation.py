import pytest
import copy

import app.main as main
import app.validation as validation


def test_generating_schema(configurations, schemas):
    """Test that the schema generation function returns the correct result."""
    for survey_name, configuration in configurations.items():
        schema = validation.SubmissionValidator._generate_validation_schema(
            configuration
        )
        assert schema == schemas[survey_name]


@pytest.fixture(scope='module')
def validator(test_surveys):
    """Provide validator for configuration-independent rule testing."""
    configuration = test_surveys['option']['configuration']  # generic survey
    return validation.SubmissionValidator.create(configuration)


def test_validate_min_chars_passing(validator):
    """Test that min_chars rule works correctly for some valid values."""
    assert validator._validate_min_chars(2, 'test', 'aa') is None
    assert validator._validate_min_chars(5, 'test', '       ') is None
    assert validator._validate_min_chars(0, 'test', '') is None


def test_validate_min_chars_failing(validator):
    """Test that min_chars rule fails correctly for some invalid values."""
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
    """Test that max_chars rule fails correctly for some invalid values."""
    with pytest.raises(AttributeError):
        validator._validate_max_chars(0, 'test', ' ')
    with pytest.raises(AttributeError):
        validator._validate_max_chars(9999, 'test', 'a' * 10000)
    with pytest.raises(AttributeError):
        validator._validate_max_chars(1, 'test', 'apple juice')


@pytest.fixture(scope='module')
def selection():
    """Provide a sample selection field submission value."""
    return {
        '1': False,
        '2': True,
        '3': True,
        '4': False,
        '5': True,
    }


def test_validate_min_select_passing(validator, selection):
    """Test that min_select rule works correctly for some valid values."""
    assert validator._validate_min_select(3, 'test', selection) is None
    assert validator._validate_min_select(0, 'test', selection) is None


def test_validate_min_select_failing(validator, selection):
    """Test that min_select rule fails correctly for some invalid values."""
    with pytest.raises(AttributeError):
        validator._validate_min_select(4, 'test', selection)
    with pytest.raises(AttributeError):
        validator._validate_min_select(99999, 'test', selection)


def test_validate_max_select_passing(validator, selection):
    """Test that max_select rule works correctly for some valid values."""
    assert validator._validate_max_select(3, 'test', selection) is None
    assert validator._validate_max_select(99, 'test', selection) is None


def test_validate_max_select_failing(validator, selection):
    """Test that max_select rule fails correctly for some invalid values."""
    with pytest.raises(AttributeError):
        validator._validate_max_select(2, 'test', selection)
    with pytest.raises(AttributeError):
        validator._validate_max_select(0, 'test', selection)


def test_validate_mandatory_passing(validator):
    """Test that mandatory rule works correctly for some valid values."""
    assert validator._validate_mandatory(True, 'test', True) is None
    assert validator._validate_mandatory(False, 'test', True) is None
    assert validator._validate_mandatory(False, 'test', False) is None
    assert validator._validate_mandatory(True, 'test', 'chicken') is None
    assert validator._validate_mandatory(False, 'test', '') is None
    assert validator._validate_mandatory(False, 'test', 'duck') is None


def test_validate_mandatory_failing(validator):
    """Test that mandatory rule fails correctly for some invalid values."""
    with pytest.raises(AttributeError):
        validator._validate_mandatory(True, 'test', False)
    with pytest.raises(AttributeError):
        validator._validate_mandatory(True, 'test', '')
