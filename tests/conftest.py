import pytest
import asyncio
import json

import app.survey as sve
import app.authentication as auth
import app.resources.database as database
import app.email as email
import tests.data as data


################################################################################
# Event Loop Management
################################################################################


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
# Test Data Loading (Surveys)
################################################################################


@pytest.fixture(scope='session')
def configurations():
    """Convenience method to access test survey configurations."""
    return data.TEST_SURVEY_DOCUMENTSS['configurations']


@pytest.fixture(scope='session')
def invalid_configurationss():
    """Convenience method to access invalid survey configurations."""
    return data.TEST_SURVEY_DOCUMENTSS['invalid_configurationss']


@pytest.fixture(scope='session')
def submissionss():
    """Convenience method to access test survey submissions."""
    return data.TEST_SURVEY_DOCUMENTSS['submissionss']


@pytest.fixture(scope='session')
def invalid_submissionss():
    """Convenience method to access invalid survey submissions."""
    return data.TEST_SURVEY_DOCUMENTSS['invalid_submissionss']


@pytest.fixture(scope='session')
def aggregation_pipelines():
    """Convenience method to access test survey aggregation pipelines."""
    return data.TEST_SURVEY_DOCUMENTSS['aggregation_pipelines']


@pytest.fixture(scope='session')
def resultss():
    """Convenience method to access test survey results."""
    return data.TEST_SURVEY_DOCUMENTSS['resultss']


################################################################################
# Convenience Methods To Access Test Data Of A Generic Survey
################################################################################


@pytest.fixture(scope='session')
def survey_name():
    """Convenience method to access the name of a generic configuration."""
    return 'complex'


@pytest.fixture(scope='session')
def configuration(survey_name, configurations):
    """Convenience method to access a generic valid test configuration."""
    return configurations[survey_name]


@pytest.fixture(scope='session')
def submissions(survey_name, submissionss):
    """Convenience method to access valid submissions of a generic survey."""
    return submissionss[survey_name]


################################################################################
# Test Data Loading (Accounts)
################################################################################


@pytest.fixture(scope='session')
def account_datas():
    """Convenience method to access test account datas."""
    return data.TEST_ACCOUNT_DOCUMENTSS['account_datas']


@pytest.fixture(scope='session')
def invalid_account_datas():
    """Convenience method to access invalid account datas."""
    return data.TEST_ACCOUNT_DOCUMENTSS['invalid_account_datas']


################################################################################
# Convenience Methods To Access Account Data Of A Generic Account
################################################################################


@pytest.fixture(scope='session')
def account_data(account_datas):
    """Convenience method to access the account data of the test account."""
    return account_datas[0]


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


################################################################################
# Test Data Loading (Other)
################################################################################


@pytest.fixture(scope='session')
def variables():
    """Provide the some miscellaneous values used for testing."""
    with open('tests/data/variables.json', 'r') as e:
        return json.load(e)


################################################################################
# Setup/Teardown Fixtures
################################################################################


async def reset():
    """Purge all user and survey data locally and remotely.

    The elements from collections with custom indexes are removed, while other
    collections are simply dropped entirely.

    """
    static = {'accounts', 'configurations', 'access_tokens'}
    for name in static:
        await database.database[name].delete_many({})
    other = await database.database.list_collection_names()
    for name in set(other) - static:
        await database.database[name].drop()


@pytest.fixture(scope='session', autouse=True)
async def setup():
    """Reset database before the first test starts."""
    await reset()


@pytest.fixture(scope='function')
async def cleanup():
    """Reset database after a single test."""
    yield
    await reset()


################################################################################
# Monkey Patches
################################################################################


@pytest.fixture(scope='function')
def mock_email_sending(monkeypatch):
    """Mock email sending to avoid constantly sending real emails."""
    async def _send(*args):
        return 200
    monkeypatch.setattr(email, '_send', _send)


@pytest.fixture(scope='function')
def mock_token_generation(monkeypatch):
    """Mock token generation for predictable tokens with duplicates.

    Duplicate tokens account for potential token collisions in the actual
    token creation function. The tokens that are used after duplication
    resolution are: 0, 1, 2, ... (padded with zeros to a length of 64)

    """
    global counter
    counter = -1
    def generate_token():
        global counter
        counter += 1
        return str(counter//4).zfill(64)
    monkeypatch.setattr(auth, 'generate_token', generate_token)


def valid_token():
    """Get the most recent token issued by mock token generation function."""
    global counter
    return str(counter//4).zfill(64)


def invalid_token():
    """Get a token that is not the most recently issued mock token."""
    global counter
    return str(counter//4+1).zfill(64)

