import asyncio
import pytest

from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient

from .. import main


@pytest.fixture(autouse=True)
def config(event_loop):
    """Reconfigure motor client's event loop and database before every test."""
    # rebind event loop of the motor client
    main.motor_client = AsyncIOMotorClient(main.MDBCSTR, io_loop=event_loop)
    # rebind database to testing database
    main.db = main.motor_client['async_survey_database_testing']
    # rebind surveys with new testing database
    main.surveys = main.create_surveys(main.db)


@pytest.fixture
async def cleanup():
    """Delete all pending and verified entries in the testing collections.

    To avoid deleting real survey entries due to some fault in the database
    remapping, we restrict deletion to the test-survey entries
    
    """
    yield
    await main.db['pending'].delete_many({'survey': 'test-survey'})
    await main.db['verified'].delete_many({'survey': 'test-survey'})


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
        'email': 'tt00est@mytum.de',
        'properties': {
            'election': {
                'felix': True,
                'moritz': True,
                'andere': '',
            },
            'reason': 'insert very good reason here',
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


@pytest.mark.asyncio
async def test_submit_invalid_submission(cleanup):
    """Test that submit correctly rejects an invalid test survey submission."""
    submission = {
        'email': 'tt00est@mytum.de',
        'properties': {
            'election': {
                'felix': 5,  # should be a boolean instead of an integer
                'moritz': True,
                'andere': '',
            },
            'reason': 'insert very good reason here',
        },
    }
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.post(url='/test-survey/submit', json=submission)
    entry = await main.db['pending'].find_one(projection={'_id': False})
    assert response.status_code == 400
    assert entry is None


@pytest.fixture
async def setup():
    """Load some predefined entries into the database to test verification."""
    await main.db['pending'].insert_many([
        {
            'survey': 'test-survey',
            'email': 'tt00est@mytum.de',
            'properties': {'data': 'cucumber'},
            'timestamp': 1590228251,
            'token': 'tomato',
        },
        {
            'survey': 'test-survey',
            'email': 'tt01est@mytum.de',
            'properties': {'data': 'salad'},
            'timestamp': 1590228461,
            'token': 'carrot',
        },
    ])
    await main.db['verified'].insert_many([
        {
            'survey': 'test-survey',
            'email': 'tt02est@mytum.de',
            'properties': {'data': 'radish'},
            'timestamp': 1590228043,
        },
        {
            'survey': 'test-survey',
            'email': 'tt00est@mytum.de',
            'properties': {'data': 'cabbage'},
            'timestamp': 1590228136,
        },
    ])


@pytest.mark.xfail
@pytest.mark.asyncio
async def test_verify_valid_token(setup, cleanup):
    """Test correct verification given a valid submission token."""
    token = 'tomato'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/test-survey/verify/{token}',
            allow_redirects=False,
        )
    pending = await main.db['pending'].find(
        filter={'email': 'tt00est@mytum.de'},
        projection={'_id': False}
    ).to_list(5)
    verified = await main.db['verified'].find(
        filter={'email': 'tt00est@mytum.de'},
        projection={'_id': False}
    ).to_list(5)
    keys = {'survey', 'email', 'properties', 'timestamp'}
    assert response.status_code == 307
    assert len(pending) == 0  # entry is no more in pending entries
    assert len(verified) == 1  # entry replaces previously verified entry
    assert set(verified[0].keys()) == keys
    assert verified[0]['properties']['data'] == 'cucumber'
    

@pytest.mark.asyncio
async def test_verify_invalid_token(setup, cleanup):
    """Test correct verification rejection given an invalid token."""
    token = 'peach'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/test-survey/verify/{token}',
            allow_redirects=False,
        )
    pending = await main.db['pending'].find(
        filter={'email': 'tt00est@mytum.de'},
        projection={'_id': False}
    ).to_list(5)
    verified = await main.db['verified'].find(
        filter={'email': 'tt00est@mytum.de'},
        projection={'_id': False}
    ).to_list(5)
    assert response.status_code == 401
    assert len(pending) == 1  # entry is still in pending entries
    assert len(verified) == 1  # old entry is still present
    assert verified[0]['properties']['data'] == 'cabbage'
