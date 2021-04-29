import pytest
import secrets
import httpx

import app.main as main


@pytest.mark.asyncio
async def test_fetching_configuration_with_valid_identifier(
        username,
        configurationss,
    ):
    """Using valid survey identifier, test that correct config is returned."""
    for survey_name, configurations in configurationss.items():
        async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
            url = f'/users/{username}/surveys/{survey_name}'
            response = await c.get(url)
        assert response.status_code == 200
        assert response.json() == configurations['valid']


@pytest.mark.asyncio
async def test_fetching_configuration_with_invalid_identifier(username):
    """Using invalid survey identifier, test that an exception is raised."""
    async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
        url = f'/users/{username}/surveys/carrot'
        response = await c.get(url)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submitting_valid_submission(username, submissionss, cleanup):
    """Test that submission works with valid submissions for test surveys."""
    async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
        for survey_name, submissions in submissionss.items():
            survey = await main.survey_manager.fetch(username, survey_name)
            url = f'/users/{username}/surveys/{survey_name}/submissions'
            for submission in submissions['valid']:
                response = await c.post(url, json=submission)
                assert response.status_code == 200
                entry = await survey.submissions.find_one({'data': submission})
                assert entry is not None


@pytest.mark.asyncio
async def test_submitting_invalid_submission(
        username,
        submissionss,
        cleanup,
    ):
    """Test that submit correctly fails for invalid test survey submissions."""
    async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
        for survey_name, submissions in submissionss.items():
            survey = await main.survey_manager.fetch(username, survey_name)
            url = f'/users/{username}/surveys/{survey_name}/submissions'
            for submission in submissions['invalid']:
                response = await c.post(url, json=submission)
                assert response.status_code == 400
                entry = await survey.submissions.find_one()
                assert entry is None


@pytest.mark.asyncio
async def test_duplicate_validation_token_resolution(
        monkeypatch,
        username,
        submissionss,
        cleanup,
    ):
    """Test that duplicate tokens in submissions are correctly resolved."""
    survey_name = 'complex-survey'
    survey = await main.survey_manager.fetch(username, survey_name)
    submissions = submissionss[survey_name]['valid']
    tokens = []

    def token(length):
        """Return predefined tokens in order to test token validation."""
        tokens.append(str(len(tokens) // 3))
        return tokens[-1]

    monkeypatch.setattr(secrets, 'token_hex', token)  # mock token generation
    async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
        for i, submission in enumerate(submissions):
            response = await c.post(
                url=f'/users/{username}/surveys/{survey_name}/submissions',
                json=submission,
            )
            assert response.status_code == 200
            entry = await survey.submissions.find_one({'data': submission})
            assert entry is not None
            assert entry['_id'] == str(i)


@pytest.mark.asyncio
async def test_verifying_valid_token(
        monkeypatch,
        username,
        submissionss,
        cleanup,
    ):
    """Test correct verification given a valid submission token."""
    survey_name = 'complex-survey'
    survey = await main.survey_manager.fetch(username, survey_name)
    submissions = submissionss[survey_name]['valid']
    tokens = []

    def token(length):
        """Return predefined tokens in order to test token validation."""
        tokens.append(str(len(tokens)))
        return tokens[-1]

    monkeypatch.setattr(secrets, 'token_hex', token)  # token generation mock
    async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
        base_url = f'/users/{username}/surveys/{survey_name}'
        for submission in submissions:
            await c.post(f'{base_url}/submission', json=submission)
        for i, token in enumerate(tokens):
            response = await c.get(
                url=f'{base_url}/verification/{token}',
                allow_redirects=False,
            )
            assert response.status_code == 307
            entry = await survey.submissions.find_one({'_id': token})
            ve = await survey.vss.find_one({'_id': f'test+{i}@fastsurvey.io'})
            assert entry is not None  # still unchanged in submissions
            assert ve is not None  # now also in verified submissions


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
async def test_verifying_replace_valid_token(scenario2, survey):
    """Test replacement of previously verified submission."""
    token = 'tomato'
    async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
        response = await c.get(
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
async def test_verifying_invalid_token(scenario2, survey):
    """Test correct verification rejection given an invalid token."""
    token = 'peach'
    async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
        response = await c.get(
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
async def test_verifying_with_no_prior_submission(survey):
    token = 'olive'
    async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
        response = await c.get(
            url=f'/fastsurvey/test/verify/{token}',
            allow_redirects=False,
        )
    pe = await survey.pending.find_one()
    ve = await survey.verified.find_one()
    assert response.status_code == 401
    assert pe is None
    assert ve is None


@pytest.mark.asyncio
async def test_aggregating(username, submissionss, resultss, cleanup):
    """Test that aggregation of test submissions returns the correct result."""
    for survey_name, submissions in submissionss.items():
        # push test submissions
        survey = await main.survey_manager.fetch(username, survey_name)
        await survey.alligator.collection.insert_many([
            {'data': submission}
            for submission
            in submissions['valid']
        ])
        # manually close survey so that we can aggregate
        survey.end = 0
        # aggregate and fetch results
        async with httpx.AsyncClient(app=main.app, base_url='http://test') as c:
            response = await c.get(
                url=f'/users/{username}/surveys/{survey_name}/results',
                allow_redirects=False,
            )
        assert response.status_code == 200
        assert response.json() == resultss[survey_name]
