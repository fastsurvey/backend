import pytest
import asyncio
import json
import os

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
def configurations():
    """Provide a dictionary mapping of test survey names to configurations."""
    folder = 'tests/surveys'
    survey_names = [
        os.path.splitext(file)[0]
        for file
        in os.listdir(folder)
        if os.path.splitext(file)[1] == '.json'
    ]
    configurations = {}
    for survey_name in survey_names:
        with open(f'{folder}/{survey_name}.json', 'r') as configuration:
            configurations[survey_name] = json.load(configuration)
    return configurations


async def reset(configurations):
    """Purge all survey data locally and remotely and reset configurations."""
    for survey_name in configurations.keys():
        await main.manager.delete('fastsurvey', survey_name)
    await main.database['configurations'].drop()
    for configuration in configurations.values():
        await main.manager.update(configuration)


@pytest.fixture(scope='session', autouse=True)
async def setup(configurations):
    """Reset survey data and configurations before the first test starts."""
    await reset(configurations)


@pytest.fixture(scope='function')
async def cleanup(configurations):
    """Reset survey data and configurations after a single test."""
    yield
    await reset(configurations)


@pytest.fixture(scope='function')
def submission():
    """Provide a correct sample submission for the test survey."""
    return {
        'email': 'aa00aaa@mytum.de',
        'properties': {
            '1': {
                '1': True,
                '2': False,
            },
            '2': {
                '1': True,
                '2': True,
                '3': False,
            },
            '3': 'hello world!',
        }
    }
