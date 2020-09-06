import pytest
import secrets

from httpx import AsyncClient

import app.main as main


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
    configuration = await main.database['configurations'].find_one(
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


@pytest.mark.asyncio
async def test_submit_valid_submission(survey, submission):
    """Test that submit works with a valid submission for the test survey."""
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.post(
            url='/fastsurvey/test/submit',
            json=submission,
        )
    pe = await survey.pending.find_one()
    keys = {'_id', 'email', 'timestamp', 'properties'}
    assert response.status_code == 200
    assert set(pe.keys()) == keys
    assert pe['email'] == submission['email']
    assert pe['properties'] == submission['properties']


@pytest.mark.asyncio
async def test_submit_invalid_submission(survey, submission):
    """Test that submit correctly rejects an invalid test survey submission."""
    submission['properties']['1']['1'] = 5  # should be boolean
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.post(
            url='/fastsurvey/test/submit',
            json=submission,
        )
    pe = await survey.pending.find_one()
    assert response.status_code == 400
    assert pe is None


@pytest.fixture(scope='function')
async def scenario1(survey):
    """Load some predefined entries into the database for testing."""
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
        survey,
        submission,
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
    pes = await survey.pending.find().to_list(10)
    assert response.status_code == 200
    assert len(pes) == len(tokens)
    for token, pe in zip(tokens, pes):
        assert pe['_id'] == token


@pytest.mark.asyncio
async def test_verify_valid_token(scenario1, survey):
    """Test correct verification given a valid submission token."""
    token = 'tomato'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/fastsurvey/test/verify/{token}',
            allow_redirects=False,
        )
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
async def scenario2(survey):
    """Load some predefined entries into the database for testing."""
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
async def test_verify_replace_valid_token(scenario2, survey):
    """Test replacement of previously verified submission."""
    token = 'tomato'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/fastsurvey/test/verify/{token}',
            allow_redirects=False,
        )
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
async def test_verify_invalid_token(scenario2, survey):
    """Test correct verification rejection given an invalid token."""
    token = 'peach'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/fastsurvey/test/verify/{token}',
            allow_redirects=False,
        )
    pes = await survey.pending.find().to_list(10)
    ve = await survey.verified.find_one(
        filter={'_id': 'aa00aaa@mytum.de'},
    )
    assert response.status_code == 401
    assert len(pes) == 2  # entries are unchanged in pending entries
    assert ve is not None  # old entry is still present
    assert ve['properties']['1'] == 'radish'


@pytest.mark.asyncio
async def test_verify_with_no_prior_submission(survey):
    token = 'olive'
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/fastsurvey/test/verify/{token}',
            allow_redirects=False,
        )
    pe = await survey.pending.find_one()
    ve = await survey.verified.find_one()
    assert response.status_code == 401
    assert pe is None
    assert ve is None


@pytest.fixture(scope='function')
async def scenario3(survey):
    """Load some predefined entries into the database for testing."""
    await survey.verified.insert_many([
        {
            '_id': 'aa01aaa@mytum.de',
            'timestamp': 1590228136,
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
                '3': 'tomato! tomato! tomato!',
            },
        },
        {
            '_id': 'aa02aaa@mytum.de',
            'timestamp': 1590228136,
            'properties': {
                '1': {
                    '1': True,
                    '2': False,
                },
                '2': {
                    '1': True,
                    '2': False,
                    '3': False,
                },
                '3': 'apple! apple! apple!',
            },
        },
        {
            '_id': 'aa03aaa@mytum.de',
            'timestamp': 1590228136,
            'properties': {
                '1': {
                    '1': False,
                    '2': True,
                },
                '2': {
                    '1': False,
                    '2': True,
                    '3': False,
                },
                '3': 'cabbage! cabbage! cabbage!',
            },
        },
    ])


@pytest.mark.asyncio
async def test_fetch(scenario3):
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get(
            url=f'/fastsurvey/test/results',
            allow_redirects=False,
        )
    assert response.status_code == 200
    assert response.json() == {
        '_id': 'fastsurvey.test',
        'count': 3,
        '1-1': 2,
        '1-2': 1,
        '2-1': 2,
        '2-2': 2,
        '2-3': 0,
    }
