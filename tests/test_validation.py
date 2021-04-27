import pytest
import copy

import app.main as main
import app.validation as validation


@pytest.fixture(scope='module')
def account_validator():
    """Provide an instance of the account validator."""
    return validation.AccountValidator()


@pytest.fixture(scope='module')
def configuration_validator():
    """Provide an instance of the configuration validator."""
    return validation.ConfigurationValidator.create()


@pytest.fixture(scope='module')
def submission_validators(configurations):
    """Provide submission validator for every test survey."""
    return {
        survey_name: validation.SubmissionValidator.create(configuration)
        for survey_name, configuration
        in configurations.items()
    }

################################################################################
# Account Validation
################################################################################


def test_accounts_passing(account_validator, accounts):
    """Test that account validator passes some valid submissions."""
    for account_data in accounts['valid']:
        assert account_validator.validate(account_data)


def test_accounts_failing(account_validator, accounts):
    """Test that account validator fails some invalid submissions."""
    for account_data in accounts['invalid']:
        assert not account_validator.validate(account_data)


################################################################################
# Configuration Validation
################################################################################

################################################################################
# Submission Validation
################################################################################


def test_generating_submission_validation_schema(configurations, schemas):
    """Test that the schema generation function returns the correct result."""
    for survey_name, configuration in configurations.items():
        schema = validation.SubmissionValidator._generate_validation_schema(
            configuration
        )
        assert schema == schemas[survey_name]


def test_submissions_passing(submission_validators, submissionss):
    """Test that submission validator passes some valid submissions."""
    for survey_name, submissions in submissionss.items():
        for submission in submissions['valid']:
            assert submission_validators[survey_name].validate(submission)


def test_submissions_failing(submission_validators, submissionss):
    """Test that submission validator fails some invalid submissions."""
    for survey_name, submissions in submissionss.items():
        for submission in submissions['invalid']:
            assert not submission_validators[survey_name].validate(submission)
