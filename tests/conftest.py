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
def survey_names():
    """Provide the names of all available test surveys."""
    folder = 'tests/surveys'
    return [
        os.path.splitext(file)[0]
        for file
        in os.listdir(folder)
        if os.path.splitext(file)[1] == '.json'
    ]


@pytest.fixture(scope='session')
def configurations(survey_names):
    folder = 'tests/surveys'
    configurations = {}
    for survey_name in survey_names:
        with open(f'{folder}/{survey_name}.json', 'r') as configuration:
            configurations[survey_name] = json.load(configuration)
    return configurations


@pytest.fixture(scope='function')
async def synchronize(configurations):
    """Synchronize local (JSON) test survey configurations to the database."""
    main.database['configurations'].drop()
    for configuration in configurations.values():
        await main.manager.update(configuration)


@pytest.fixture(scope='function')
async def cleanup(survey_names):
    """Purge all survey data locally and on the database after a test."""
    yield
    for survey_name in survey_names:
        await main.manager.delete('fastsurvey', survey_name)


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
