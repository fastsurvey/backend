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
def accounts():
    """Provide some valid and invalid example test accounts."""
    with open('tests/data/accounts.json', 'r') as e:
        return json.load(e)


@pytest.fixture(scope='session')
def account_data(accounts):
    """Convenience method to access the account data of the test account."""
    return accounts['valid'][0]


@pytest.fixture(scope='session')
def username(account_data):
    """Convenience method to access the username of the test account."""
    return account_data['username']


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


async def reset(username, account_data, configurationss):
    """Purge all user and survey data locally and remotely and reset it."""

    # motor transaction example

    '''

    async with await main.motor_client.start_session() as session:
        async with session.start_transaction():
            #await main.database['toast'].rename('toast-reloaded')
            #await main.database['toast-reloaded'].insert_one({'value': 'hello!'})
            #await main.database['toast-reloaded'].rename('toast-reloaded-two')
            #await main.database['toast-reloaded-two'].drop()
            #await main.database['japan'].insert_one({'value': 'what?'})
            result = await main.database['japan'].replace_one(
                filter={'value': 'what?'},
                replacement={'password': 'lol'},
            )
            await main.database['japan'].insert_one({'value': result.matched_count})


    async with await self.motor_client.start_session() as session:
        async with session.start_transaction():

            # TODO rename results

            result = await self.database['configurations'].replace_one(
                filter=expression,
                replacement=configuration,
            )
            if result.matched_count == 0:
                raise HTTPException(400, 'not an existing survey')

            collection_names = await self.database.list_collection_names()
            old_cname = (
                f'surveys'
                f'.{combine(username, survey_name)}'
                f'.submissions'
            )
            new_cname = (
                f'surveys'
                f'.{combine(username, configuration["survey_name"])}'
                f'.submissions'
            )
            if old_cname in collection_names:
                self.database[old_cname].rename(new_cname)

            old_cname = f'{old_cname}.verified'
            new_cname = f'{new_cname}.verified'
            if old_cname in collection_names:
                self.database[old_cname].rename(new_cname)

    '''

    await main.account_manager.delete(username)
    await main.account_manager.create(username, account_data)
    for survey_name, configurations in configurationss.items():
        await main.survey_manager.create(
            username,
            survey_name,
            copy.deepcopy(configurations['valid']),
        )


@pytest.fixture(scope='session', autouse=True)
async def setup(username, account_data, configurationss):
    """Reset survey data and configurations before the first test starts."""
    await reset(username, account_data, configurationss)


@pytest.fixture(scope='function')
async def cleanup(username, account_data, configurationss):
    """Reset survey data and configurations after a single test."""
    yield
    await reset(username, account_data, configurationss)
