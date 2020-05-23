import asyncio
import pytest

from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient

from .. import main


@pytest.fixture(autouse=True)
def config(event_loop):
    """Reconfigure motor client's event loop and database before every test."""
    # rebingd event loop of the motor client
    main.motor_client = AsyncIOMotorClient(main.MDBCSTR, io_loop=event_loop)
    # rebind database to testing database
    main.db = main.motor_client['async_survey_database_testing']
    # rebind surveys with new testing database
    main.surveys = main.create_surveys(main.db)


@pytest.fixture
async def cleanup(config):
    """Delete all pending and verified entries in the testing collections.

    To avoid deleting real survey entries due to some fault in the database
    remapping, we restrict deletion to the testing email.
    
    """
    yield
    await main.db['pending'].delete_many({'email': 'test123@mytum.de'})
    await main.db['verified'].delete_many({'email': 'test123@mytum.de'})


@pytest.mark.asyncio
async def test_status_passing():
    """Test that status function returns that all services are operational."""
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get('/')
    assert response.status_code == 200
    assert response.json() == {'status': 'all services operational'}


@pytest.mark.asyncio
async def test_submit_valid_submission(cleanup):
    """Test that submit works with a valid submission for the test survey."""
    submission = {
        'email': 'test123@mytum.de',
        'properties': {
            'election': {
                'felix': True,
                'moritz': True,
                'andere': '',
            },
            'reason': '',
        },
    }
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.post(url='/test-survey/submit', json=submission)
        entry = await main.db['pending'].find_one(projection={'_id': False})
    keys = {'survey', 'email', 'properties', 'timestamp', 'token'}
    assert response.status_code == 200
    assert set(entry.keys()) == keys
    assert entry['email'] == submission['email']
    assert entry['properties'] == submission['properties']
    assert entry['survey'] == 'test-survey'


@pytest.fixture
async def setup():
    await main.db['pending'].insert_many([
        {
            'survey': 'test-survey',
            'email': 'test123@mytum.de',
            'properties': {},
            'timestamp': 1590228251,
            'token': 'tomato',
        },
        {
            'survey': 'test-survey',
            'email': 'test123@mytum.de',
            'properties': {},
            'timestamp': 1590228461,
            'token': 'carrot',
        },
    ])


@pytest.mark.asyncio
async def test_verify_valid_token(setup, cleanup):
    token = 'tomato'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/test-survey/verify/{token}',
            allow_redirects=False,
        )
    assert response.status_code == 307
    # test if in verified entries
    # test that not in pending entries


# test that verify replaces previously verified entries