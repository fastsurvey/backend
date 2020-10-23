import pytest
import secrets

from httpx import AsyncClient

import app.main as main


@pytest.mark.asyncio
async def test_fetching_configuration_with_valid_identifier(test_surveys):
    """Using valid survey identifier, test that correct config is returned."""
    for survey_name, parameters in test_surveys.items():
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.get(f'/admins/fastsurvey/surveys/{survey_name}')
        assert response.status_code == 200
        assert response.json() == parameters['configuration']


@pytest.mark.asyncio
async def test_fetching_configuration_with_invalid_identifier():
    """Using invalid survey identifier, test that an exception is raised."""
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        response = await ac.get('admins/fastsurvey/surveys/carrot')
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_valid_submission(test_surveys, cleanup):
    """Test that submit works with valid submissions for test surveys."""
    for survey_name, parameters in test_surveys.items():
        for submission in parameters['submissions']['valid']:
            async with AsyncClient(app=main.app, base_url='http://test') as ac:
                response = await ac.post(
                    url=f'/admins/fastsurvey/surveys/{survey_name}/submission',
                    json=submission,
                )
            survey = await main.survey_manager.fetch('fastsurvey', survey_name)
            entry = await survey.submissions.find_one({'data': submission})
            assert response.status_code == 200
            assert entry is not None


@pytest.mark.asyncio
async def test_submit_invalid_submission(test_surveys, cleanup):
    """Test that submit correctly fails for invalid test survey submissions."""
    for survey_name, parameters in test_surveys.items():
        for submission in parameters['submissions']['invalid']:
            async with AsyncClient(app=main.app, base_url='http://test') as ac:
                response = await ac.post(
                    url=f'/admins/fastsurvey/surveys/{survey_name}/submission',
                    json=submission,
                )
            survey = await main.survey_manager.fetch('fastsurvey', survey_name)
            entry = await survey.submissions.find_one()
            assert response.status_code == 400
            assert entry is None


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


@pytest.mark.skip(reason='scheduled for refactoring')
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
            url='/admins/fastsurvey/surveys/test/submission',
            json=submission,
        )
    pes = await survey.pending.find().to_list(10)
    assert response.status_code == 200
    assert len(pes) == len(tokens)
    for token, pe in zip(tokens, pes):
        assert pe['_id'] == token


@pytest.mark.asyncio
async def test_verify_valid_token(monkeypatch, test_surveys, cleanup):
    """Test correct verification given a valid submission token."""
    survey_name = 'complex-survey'
    survey = await main.survey_manager.fetch('fastsurvey', survey_name)
    base = f'/admins/fastsurvey/surveys/{survey_name}'
    tokens = []

    def token(length):
        """Return predefined tokens in order to test token token validation."""
        tokens.append(str(len(tokens)))
        return tokens[-1]

    monkeypatch.setattr(secrets, 'token_hex', token)  # token generation mock
    async with AsyncClient(app=main.app, base_url='http://test') as ac:
        for submission in test_surveys[survey_name]['submissions']['valid']:
            await ac.post(
                url=f'{base}/submission',
                json=submission,
            )
        for i, token in enumerate(tokens):
            response = await ac.get(
                url=f'{base}/verification/{token}',
                allow_redirects=False,
            )
            assert response.status_code == 307
            pe = await survey.submissions.find_one({'_id': token})
            ve = await survey.vss.find_one({'_id': f'test+{i}@fastsurvey.io'})
            assert pe is not None  # entry still unchanged in submissions
            assert ve is not None  # entry now also in verified submissions


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


@pytest.mark.skip(reason='scheduled for refactoring')
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


@pytest.mark.skip(reason='scheduled for refactoring')
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


@pytest.mark.skip(reason='scheduled for refactoring')
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


@pytest.mark.asyncio
async def test_aggregate(test_surveys, cleanup):
    """Test that aggregation of test submissions returns the correct result."""
    for survey_name, parameters in test_surveys.items():
        # push test submissions
        survey = await main.survey_manager.fetch('fastsurvey', survey_name)
        await survey.alligator.collection.insert_many([
            {'data': submission}
            for submission
            in parameters['submissions']['valid']
        ])
        # manually close surveys so that we can aggregate
        survey.end = 0
        # aggregate and fetch results
        async with AsyncClient(app=main.app, base_url='http://test') as ac:
            response = await ac.get(
                url=f'/admins/fastsurvey/surveys/{survey_name}/results',
                allow_redirects=False,
            )
        assert response.status_code == 200
        assert response.json() == parameters['results']
