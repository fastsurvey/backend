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


def read(folder):
    """Provide mapping of test survey names to JSON data in given folder."""
    survey_names = [
        os.path.splitext(file)[0]
        for file
        in os.listdir(folder)
        if os.path.splitext(file)[1] == '.json'
    ]
    xs = {}
    for survey_name in survey_names:
        with open(f'{folder}/{survey_name}.json', 'r') as x:
            xs[survey_name] = json.load(x)
    return xs


@pytest.fixture(scope='session')
def configurations():
    """Provide mapping of test survey names to their configurations."""
    folder = 'tests/surveys/configurations'
    return read(folder)


@pytest.fixture(scope='session')
def schemas():
    """Provide mapping of test survey names to their validation schemas."""
    folder = 'tests/surveys/schemas'
    return read(folder)


@pytest.fixture(scope='session')
def valid_submissions():
    """Provide mapping of test survey names to valid submissions."""
    folder = 'tests/surveys/valid-submissions'
    return read(folder)


async def reset(configurations):
    """Purge all survey data locally and remotely and reset configurations."""
    for survey_name in configurations.keys():
        await main.survey_manager.delete('fastsurvey', survey_name)
    await main.database['configurations'].drop()
    for configuration in configurations.values():
        await main.survey_manager.update(configuration)


@pytest.fixture(scope='session', autouse=True)
async def setup(configurations):
    """Reset survey data and configurations before the first test starts."""
    await reset(configurations)


@pytest.fixture(scope='function')
async def cleanup(configurations):
    """Reset survey data and configurations after a single test."""
    yield
    await reset(configurations)
