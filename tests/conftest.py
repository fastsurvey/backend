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
def test_surveys():
    """Provide mapping of test survey names to their testing parameters."""
    folder = 'tests/surveys'
    survey_names = [e for e in os.listdir(folder) if e[0] != '.']
    ts = {}
    for survey_name in survey_names:
        subfolder = f'{folder}/{survey_name}'
        parameter_names = [
            os.path.splitext(e)[0]
            for e
            in os.listdir(subfolder)
            if os.path.splitext(e)[1] == '.json'
        ]
        ts[survey_name] = dict()
        for parameter_name in parameter_names:
            with open(f'{subfolder}/{parameter_name}.json', 'r') as e:
                ts[survey_name][parameter_name] = json.load(e)
    return ts


async def reset(test_surveys):
    """Purge all survey data locally and remotely and reset configurations."""
    for survey_name in test_surveys.keys():
        await main.survey_manager.delete('fastsurvey', survey_name)
    for survey_name, parameters in test_surveys.items():
        await main.survey_manager.update(
            'fastsurvey',
            survey_name,
            parameters['configuration'],
        )


@pytest.fixture(scope='session', autouse=True)
async def setup(test_surveys):
    """Reset survey data and configurations before the first test starts."""
    await reset(test_surveys)


@pytest.fixture(scope='function')
async def cleanup(test_surveys):
    """Reset survey data and configurations after a single test."""
    yield
    await reset(test_surveys)
