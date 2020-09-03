import pytest
import asyncio

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


@pytest.fixture(scope='function')
async def survey():
    """Provide an instant of the test survey."""
    return await main.manager.get('fastsurvey', 'test')


@pytest.fixture(scope='function', autouse=True)
async def cleanup(survey):
    """Clean up database and survey instants after each test."""
    yield
    idd = {'_id': 'fastsurvey.test'}
    await survey.pending.drop()
    await survey.verified.drop()
    await survey.alligator.results.delete_one(idd)
    cn = await main.database['configurations'].find_one(idd)
    main.manager.add(cn)


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
