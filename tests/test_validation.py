import pytest
import pydantic

import app.validation as validation


################################################################################
# Account Validation
################################################################################


def test_account_data_passing(account_datas):
    """Test that account validation passes some valid accounts."""
    for account_data in account_datas:
        validation.AccountData(**account_data)


def test_account_data_failing(invalid_account_datas):
    """Test that account validation fails some invalid accounts."""
    for account_data in invalid_account_datas:
        with pytest.raises(pydantic.ValidationError):
            validation.AccountData(**account_data)


################################################################################
# Configuration Validation
################################################################################


def test_configurations_passing(configurations):
    """Test that configuration validation passes some valid configurations."""
    for configuration in configurations.values():
        validation.Configuration(**configuration)


def test_configurations_failing(invalid_configurationss):
    """Test that configuration validation fails some invalid configurations."""
    for invalid_configurations in invalid_configurationss.values():
        for configuration in invalid_configurations:
            with pytest.raises(pydantic.ValidationError):
                validation.Configuration(**configuration)


################################################################################
# Submission Validation
################################################################################


def test_submissions_passing(configurations, submissionss):
    """Test that submission validation passes some valid submissions."""
    for survey_name, submissions in submissionss.items():
        Submission = validation.build_submission_model(
            validation.Configuration(**configurations[survey_name])
        )
        for submission in submissions:
            Submission(**submission)


def test_submissions_failing(configurations, invalid_submissionss):
    """Test that submission validation fails some invalid submissions."""
    for survey_name, invalid_submissions in invalid_submissionss.items():
        Submission = validation.build_submission_model(
            validation.Configuration(**configurations[survey_name])
        )
        for submission in invalid_submissions:
            with pytest.raises(pydantic.ValidationError):
                Submission(**submission)
