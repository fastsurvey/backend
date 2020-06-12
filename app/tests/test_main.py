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
    # rebind surveys with new testing database
    main.surveys = main.create_surveys()


@pytest.fixture
async def cleanup():
    """Delete all pending and verified entries in the testing collections."""
    yield
    await main.surveys['test-survey'].pending.delete_many({})
    await main.surveys['test-survey'].verified.delete_many({})


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
        'email': 'aa00aaa@mytum.de',
        'properties': {
            '1': {
                '1': True,
                '2': True,
                '3': '',
            },
            '2': 'insert very good reason here',
        },
    }
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.post(
            url='/test-survey/submit', 
            json=submission,
        )
    pe = await main.surveys['test-survey'].pending.find_one()
    keys = {'_id', 'email', 'timestamp', 'properties'}
    assert response.status_code == 200
    assert set(pe.keys()) == keys
    assert pe['email'] == submission['email']
    assert pe['properties'] == submission['properties']


@pytest.mark.asyncio
async def test_submit_invalid_submission(cleanup):
    """Test that submit correctly rejects an invalid test survey submission."""
    submission = {
        'email': 'aa00aaa@mytum.de',
        'properties': {
            '1': {
                '1': 5,  # should be a boolean instead of an integer
                '2': True,
                '3': '',
            },
            '2': 'insert very good reason here',
        },
    }
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.post(url='/test-survey/submit', json=submission)
    pe = await main.surveys['test-survey'].pending.find_one()
    assert response.status_code == 400
    assert pe is None


@pytest.fixture
async def setup():
    """Load some predefined entries into the database to test verification."""
    await main.surveys['test-survey'].pending.insert_many([
        {
            '_id': 'tomato',
            'email': 'aa00aaa@mytum.de',
            'timestamp': 1590228251,
            'properties': {'data': 'cucumber'},
        },
        {
            '_id': 'carrot',
            'email': 'aa00aaa@mytum.de',
            'timestamp': 1590228461,
            'properties': {'data': 'salad'},
        },
    ])
    await main.surveys['test-survey'].verified.insert_many([
        {
            '_id': 'aa00aaa@mytum.de',
            'timestamp': 1590228043,
            'properties': {'data': 'radish'},
        },
        {
            '_id': 'aa02aaa@mytum.de',
            'timestamp': 1590228136,
            'properties': {'data': 'cabbage'},
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
    pe = await main.surveys['test-survey'].pending.find_one(
        filter={'_id': 'tomato'},
    )
    ve = await main.surveys['test-survey'].verified.find_one(
        filter={'_id': 'aa00aaa@mytum.de'},
    )
    keys = {'_id', 'timestamp', 'properties'}
    assert response.status_code == 307
    assert pe is None  # entry is no more in pending entries
    assert ve is not None  # entry replaces previously verified entry
    assert set(ve.keys()) == keys
    assert ve['properties']['data'] == 'cucumber'
    

@pytest.mark.asyncio
async def test_verify_invalid_token(setup, cleanup):
    """Test correct verification rejection given an invalid token."""
    token = 'peach'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/test-survey/verify/{token}',
            allow_redirects=False,
        )
    pes = await main.surveys['test-survey'].pending.find().to_list(5)
    ve = await main.surveys['test-survey'].verified.find_one(
        filter={'_id': 'aa00aaa@mytum.de'},
    )
    assert response.status_code == 401
    assert len(pes) == 2  # entries are unchanged in pending entries
    assert ve is not None  # old entry is still present
    assert ve['properties']['data'] == 'radish'
