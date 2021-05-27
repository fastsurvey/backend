import pytest
import asyncio
import json
import os

import app.main as main
import app.cryptography.access as access
import app.survey as svy
import app.resources.database as database


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
    """Convenience method to access test survey configurations.

    If during testing, some general valid/invalid survey configuration is
    needed, preferably use the 'complex' survey for consistency.

    """
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


async def reset():
    """Purge all user and survey data locally and remotely.

    The elements from collections with custom indexes are removed, while other
    collections are simply dropped entirely.

    """
    static = {'accounts', 'configurations', 'resultss'}
    for name in static:
        await database.database[name].delete_many({})
    other = await database.database.list_collection_names()
    for name in set(other) - static:
        await database.database[name].drop()
    main.survey_manager.cache.reset()


@pytest.fixture(scope='session', autouse=True)
async def setup():
    """Reset database before the first test starts."""
    await reset()


@pytest.fixture(scope='function')
async def cleanup():
    """Reset database after a single test."""
    yield
    await reset()
