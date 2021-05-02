import pytest
import asyncio
import json
import os
import copy

import app.main as main
import app.cryptography.access as access


@pytest.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test case.

    Normally, pytest-asyncio would create a new loop for each test case,
    probably with the intention of not sharing resources between tests, as
    is best practice. In our case we would thus need to recreate the motor
    client and all surveys (as they depend on the motor client) for each
    test case. This severly slows the testing, which is why we in this case
    deviate from the best practice and use a single event loop for all our
    test cases.

    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


################################################################################
# Test Data Loading
################################################################################


@pytest.fixture(scope='session')
def test_survey_data():
    """Provide test survey example data (configurations, submissions, ...)."""
    folder = 'tests/data/surveys'
    survey_names = [s for s in os.listdir(folder) if s[0] != '.']
    survey_parameters = {
        'configurationss': dict(),
        'resultss': dict(),
        'schemas': dict(),
        'submissionss': dict(),
    }
    for survey_name in survey_names:
        subfolder = f'{folder}/{survey_name}'
        for parameter_name, parameter_dict in survey_parameters.items():
            with open(f'{subfolder}/{parameter_name[:-1]}.json', 'r') as e:
                parameter_dict[survey_name] = json.load(e)
    return survey_parameters


@pytest.fixture(scope='session')
def configurationss(test_survey_data):
    """Convenience method to access test survey configurations."""
    return test_survey_data['configurationss']


@pytest.fixture(scope='session')
def resultss(test_survey_data):
    """Convenience method to access test survey results."""
    return test_survey_data['resultss']


@pytest.fixture(scope='session')
def schemas(test_survey_data):
    """Convenience method to access test survey cerberus validation schemas."""
    return test_survey_data['schemas']


@pytest.fixture(scope='session')
def submissionss(test_survey_data):
    """Convenience method to access test survey submissions."""
    return test_survey_data['submissionss']


@pytest.fixture(scope='session')
def account_datas():
    """Provide some valid and invalid examples of account data."""
    with open('tests/data/account_datas.json', 'r') as e:
        return json.load(e)


@pytest.fixture(scope='session')
def account_data(account_datas):
    """Convenience method to access the account data of the test account."""
    return account_datas['valid'][0]


@pytest.fixture(scope='session')
def username(account_data):
    """Convenience method to access the username of the test account."""
    return account_data['username']


@pytest.fixture(scope='session')
def email_address(account_data):
    """Convenience method to access the email address of the test account."""
    return account_data['email_address']


@pytest.fixture(scope='session')
def password(account_data):
    """Convenience method to access the password of the test account."""
    return account_data['password']


@pytest.fixture(scope='session')
def variables():
    """Provide the some miscellaneous values used for testing."""
    with open('tests/data/variables.json', 'r') as e:
        return json.load(e)


@pytest.fixture(scope='session')
def headers(username):
    """Provide an authentication header to access protected routes."""
    access_token = access.generate(username)['access_token']
    return {'Authorization': f'Bearer {access_token}'}


################################################################################
# Setup/Teardown Fixtures
################################################################################


async def reset(account_datas, configurationss):
    """Purge all user and survey data locally and remotely and reset it."""

    # TODO implement part-resets to increase test performance?
    # e.g. start with no data in the database each test and load only what
    # we need, then only clean what needs cleaning

    for account_data in account_datas['valid']:
        await main.account_manager.delete(account_data['username'])
    await main.account_manager.create(
        account_datas['valid'][0]['username'],
        account_datas['valid'][0],
    )
    for survey_name, configurations in configurationss.items():
        await main.survey_manager.create(
            account_datas['valid'][0]['username'],
            survey_name,
            copy.deepcopy(configurations['valid']),
        )


@pytest.fixture(scope='session', autouse=True)
async def setup(account_datas, configurationss):
    """Reset survey data and configurations before the first test starts."""
    await reset(account_datas, configurationss)


@pytest.fixture(scope='function')
async def cleanup(account_datas, configurationss):
    """Reset survey data and configurations after a single test."""
    yield
    await reset(account_datas, configurationss)
