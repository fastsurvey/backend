import pytest

import app.validation as validation


@pytest.fixture(scope='module')
def account_validator():
    """Provide an instance of the account validator."""
    return validation.AccountValidator()


@pytest.fixture(scope='module')
def configuration_validator():
    """Provide an instance of the configuration validator."""
    return validation.ConfigurationValidator()


@pytest.fixture(scope='module')
def submission_validators(configurationss):
    """Provide submission validator for every test survey."""
    return {
        survey_name: validation.SubmissionValidator.create(
            configurations['valid']
        )
        for survey_name, configurations
        in configurationss.items()
    }

################################################################################
# Account Validation
################################################################################


def test_account_data_passing(account_validator, account_datas):
    """Test that account validator passes some valid account data."""
    for account_data in account_datas['valid']:
        assert account_validator.validate(account_data)


def test_account_data_failing(account_validator, account_datas):
    """Test that account validator fails some invalid account data."""
    for account_data in account_datas['invalid']:
        assert not account_validator.validate(account_data)


################################################################################
# Configuration Validation
################################################################################


def test_configurations_passing(configuration_validator, configurationss):
    """Test that configuration validator passes some valid configurations."""
    for configurations in configurationss.values():
        assert configuration_validator.validate(configurations['valid'])


def test_configurations_failing(configuration_validator, configurationss):
    """Test that configuration validator fails some invalid configurations."""
    for configurations in configurationss.values():
        for configuration in configurations['invalid']:
            assert not configuration_validator.validate(configuration)


################################################################################
# Submission Validation
################################################################################


def test_generating_submission_validation_schema(configurationss, schemas):
    """Test that the schema generation function returns the correct result."""
    for survey_name, configurations in configurationss.items():
        schema = validation.SubmissionValidator._generate_validation_schema(
            configurations['valid']
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
