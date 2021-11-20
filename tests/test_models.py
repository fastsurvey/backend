import pydantic
import pytest

import app.models as models


########################################################################################
# Account Validation
########################################################################################


def test_account_data_passing(account_datas):
    """Test that account validation passes some valid accounts."""
    for account_data in account_datas:
        models.AccountData(**account_data)


def test_account_data_failing(invalid_account_datas):
    """Test that account validation fails some invalid accounts."""
    for account_data in invalid_account_datas:
        with pytest.raises(pydantic.ValidationError):
            models.AccountData(**account_data)


########################################################################################
# Configuration Validation
########################################################################################


def test_configurations_passing(configuration):
    """Test that configuration validation passes some valid configurations."""
    models.Configuration(**configuration)


def test_configurations_failing(invalid_configurations):
    """Test that configuration validation fails some invalid configurations."""
    for configuration in invalid_configurations:
        with pytest.raises(pydantic.ValidationError):
            models.Configuration(**configuration)


########################################################################################
# Submission Validation
########################################################################################


def test_submissions_passing(configuration, submissions):
    """Test that submission validation passes some valid submissions."""
    Submission = models.build_submission_model(configuration)
    for submission in submissions:
        Submission(**submission)


def test_submissions_failing(configuration, invalid_submissions):
    """Test that submission validation fails some invalid submissions."""
    Submission = models.build_submission_model(configuration)
    for submission in invalid_submissions:
        with pytest.raises(pydantic.ValidationError):
            Submission(**submission)
