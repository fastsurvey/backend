import pytest
import asyncio
import json
import os

from copy import deepcopy

import app.main as main


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


@pytest.fixture(scope='session')
def test_survey_parameters():
    """Provide a dictionary containing parameters for the test surveys."""
    folder = 'tests/surveys'
    survey_names = [s for s in os.listdir(folder) if s[0] != '.']
    survey_parameters = {
        'configurations': dict(),
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
def configurations(test_survey_parameters):
    """Map test survey names to their test (exchange) configurations."""
    return test_survey_parameters['configurations']


@pytest.fixture(scope='session')
def resultss(test_survey_parameters):
    """Map test survey names to their test results."""
    return test_survey_parameters['resultss']


@pytest.fixture(scope='session')
def schemas(test_survey_parameters):
    """Map test survey names to their test schema."""
    return test_survey_parameters['schemas']


@pytest.fixture(scope='session')
def submissionss(test_survey_parameters):
    """Map test survey names to their test submissions."""
    return test_survey_parameters['submissionss']


@pytest.fixture(scope='session')
async def admin_name():
    """Provide admin_name of test account."""
    return 'fastsurvey'


async def reset(admin_name, configurations):
    """Purge all admin and survey data locally and remotely and reset it."""

    '''
    async with await main.motor_client.start_session() as session:
        async with session.start_transaction():
            #await main.database['toast'].rename('toast-reloaded')
            #await main.database['toast-reloaded'].insert_one({'value': 'hello!'})
            #await main.database['toast-reloaded'].rename('toast-reloaded-two')
            #await main.database['toast-reloaded-two'].drop()
            await main.database['japan'].insert_one({'value': 'what?'})
    '''

    await main.account_manager._delete(admin_name)
    await main.account_manager.create(
        admin_name=admin_name,
        email_address='support@fastsurvey.io',
        password='supersecure',
    )
    for survey_name, configuration in configurations.items():
        await main.survey_manager._create(
            admin_name=admin_name,
            survey_name=survey_name,
            configuration=deepcopy(configuration),
        )


@pytest.fixture(scope='session', autouse=True)
async def setup(admin_name, configurations):
    """Reset survey data and configurations before the first test starts."""
    await reset(admin_name, configurations)


@pytest.fixture(scope='function')
async def cleanup(admin_name, configurations):
    """Reset survey data and configurations after a single test."""
    yield
    await reset(admin_name, configurations)
