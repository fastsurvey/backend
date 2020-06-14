import asyncio
import pytest
import secrets
import copy

from httpx import AsyncClient

from .. import main


@pytest.mark.asyncio
async def test_status_passing():
    """Test that status function returns that all services are operational."""
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get('/')
    assert response.status_code == 200
    assert response.json() == {'status': 'all services operational'}


@pytest.mark.asyncio
async def test_configuration_valid_identifier():
    """Test that the correct configuration is returned for a valid survey."""
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get('/fastsurvey/test')
    configuration = await main.motor_client['main']['configurations'].find_one(
        filter={'_id': 'fastsurvey.test'},
    )
    assert response.status_code == 200
    assert response.json() == configuration


@pytest.mark.asyncio
async def test_configuration_invalid_identifier():
    """Test the error on requesting the configuration of an invalid survey."""
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get('/fastsurvey/carrot')
    assert response.status_code == 404


@pytest.fixture(scope='function')
async def cleanup():
    """Drop the pending and verified test survey collections after a test."""
    yield
    survey = await main.manager.get('fastsurvey', 'test')
    await survey.pending.drop()
    await survey.verified.drop()


@pytest.mark.asyncio
async def test_submit_valid_submission(submission, cleanup):
    """Test that submit works with a valid submission for the test survey."""
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.post(
            url='/fastsurvey/test/submit', 
            json=submission,
        )
    survey = await main.manager.get('fastsurvey', 'test')
    pe = await survey.pending.find_one()
    keys = {'_id', 'email', 'timestamp', 'properties'}
    assert response.status_code == 200
    assert set(pe.keys()) == keys
    assert pe['email'] == submission['email']
    assert pe['properties'] == submission['properties']


@pytest.mark.asyncio
async def test_submit_invalid_submission(submission, cleanup):
    """Test that submit correctly rejects an invalid test survey submission."""
    submission = copy.deepcopy(submission)
    submission['properties']['1']['1'] = 5  # should be boolean
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.post(
            url='/fastsurvey/test/submit', 
            json=submission,
        )
    survey = await main.manager.get('fastsurvey', 'test')
    pe = await survey.pending.find_one()
    assert response.status_code == 400
    assert pe is None


@pytest.fixture(scope='function')
async def scenario1():
    """Load some predefined entries into the database for testing."""
    survey = await main.manager.get('fastsurvey', 'test')
    await survey.pending.insert_many([
        {
            '_id': 'tomato',
            'email': 'aa00aaa@mytum.de',
            'timestamp': 1590228251,
            'properties': {'1': 'cucumber'},
        },
        {
            '_id': 'carrot',
            'email': 'aa00aaa@mytum.de',
            'timestamp': 1590228461,
            'properties': {'1': 'salad'},
        },
    ])
    await survey.verified.insert_many([
        {
            '_id': 'aa02aaa@mytum.de',
            'timestamp': 1590228136,
            'properties': {'1': 'cabbage'},
        },
    ])


@pytest.mark.asyncio
async def test_submit_duplicate_token(
        monkeypatch, 
        scenario1, 
        submission, 
        cleanup,
    ):
    """Test that duplicate tokens in submissions are correctly resolved."""
    i = 0
    tokens = ['tomato', 'carrot', 'cucumber']

    def token(length):
        """Return predefined tokens in order to test token collisions."""
        nonlocal i
        i += 1
        return tokens[i-1]

    # set up mocking for token generation
    monkeypatch.setattr(secrets, 'token_hex', token)
    
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.post(
            url='/fastsurvey/test/submit', 
            json=submission,
        )
    assert response.status_code == 200
    survey = await main.manager.get('fastsurvey', 'test')
    pes = await survey.pending.find().to_list(10)
    assert len(pes) == len(tokens)
    for token, pe in zip(tokens, pes):
        assert pe['_id'] == token


@pytest.mark.asyncio
async def test_verify_valid_token(scenario1, cleanup):
    """Test correct verification given a valid submission token."""
    token = 'tomato'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/fastsurvey/test/verify/{token}',
            allow_redirects=False,
        )
    survey = await main.manager.get('fastsurvey', 'test')
    pe = await survey.pending.find_one(
        filter={'_id': 'tomato'},
    )
    ve = await survey.verified.find_one(
        filter={'_id': 'aa00aaa@mytum.de'},
    )
    keys = {'_id', 'timestamp', 'properties'}
    assert response.status_code == 307
    assert pe is not None  # entry is still unchanged in pending entries
    assert ve is not None  # entry is now in verified entries
    assert set(ve.keys()) == keys
    assert ve['properties']['1'] == 'cucumber'


@pytest.fixture(scope='function')
async def scenario2():
    """Load some predefined entries into the database for testing."""
    survey = await main.manager.get('fastsurvey', 'test')
    await survey.pending.insert_many([
        {
            '_id': 'tomato',
            'email': 'aa00aaa@mytum.de',
            'timestamp': 1590228251,
            'properties': {'1': 'cucumber'},
        },
        {
            '_id': 'carrot',
            'email': 'aa00aaa@mytum.de',
            'timestamp': 1590228461,
            'properties': {'1': 'salad'},
        },
    ])
    await survey.verified.insert_many([
        {
            '_id': 'aa00aaa@mytum.de',
            'timestamp': 1590228043,
            'properties': {'1': 'radish'},
        },
        {
            '_id': 'aa02aaa@mytum.de',
            'timestamp': 1590228136,
            'properties': {'1': 'cabbage'},
        },
    ])


@pytest.mark.asyncio
async def test_verify_replace_valid_token(scenario2, cleanup):
    """Test replacement of previously verified submission."""
    token = 'tomato'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/fastsurvey/test/verify/{token}',
            allow_redirects=False,
        )
    survey = await main.manager.get('fastsurvey', 'test')
    pe = await survey.pending.find_one(
        filter={'_id': 'tomato'},
    )
    ve = await survey.verified.find_one(
        filter={'_id': 'aa00aaa@mytum.de'},
    )
    keys = {'_id', 'timestamp', 'properties'}
    assert response.status_code == 307
    assert pe is not None  # entry is still unchanged in pending entries
    assert ve is not None  # entry replaces previously verified entry
    assert set(ve.keys()) == keys
    assert ve['properties']['1'] == 'cucumber'
    

@pytest.mark.asyncio
async def test_verify_invalid_token(scenario2, cleanup):
    """Test correct verification rejection given an invalid token."""
    token = 'peach'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/fastsurvey/test/verify/{token}',
            allow_redirects=False,
        )
    survey = await main.manager.get('fastsurvey', 'test')
    pes = await survey.pending.find().to_list(10)
    ve = await survey.verified.find_one(
        filter={'_id': 'aa00aaa@mytum.de'},
    )
    assert response.status_code == 401
    assert len(pes) == 2  # entries are unchanged in pending entries
    assert ve is not None  # old entry is still present
    assert ve['properties']['1'] == 'radish'


@pytest.mark.asyncio
async def test_verify_with_no_prior_submission(cleanup):
    token = 'olive'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/fastsurvey/test/verify/{token}',
            allow_redirects=False,
        )
    survey = await main.manager.get('fastsurvey', 'test')
    pe = await survey.pending.find_one()
    ve = await survey.verified.find_one()
    assert response.status_code == 401
    assert pe is None
    assert ve is None
