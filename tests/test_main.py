import pytest
import secrets
import httpx
import copy
import time

import app.main as main
import app.resources.database as database
import app.cryptography.access as access


@pytest.fixture(scope='module')
async def client():
    """Provide a HTTPX AsyncClient that is properly closed after testing."""
    client = httpx.AsyncClient(
        app=main.app,
        base_url='http://example.com',
    )
    yield client
    await client.aclose()


################################################################################
# Fetch User
################################################################################


@pytest.mark.asyncio
async def test_fetching_existing_user_with_valid_access_token(
        client,
        headers,
        account_data,
        username,
        cleanup,
    ):
    """Test that correct account data is returned on valid request."""
    await main.account_manager.create(username, account_data)
    response = await client.get(f'/users/{username}', headers=headers)
    assert response.status_code == 200
    keys = set(response.json().keys())
    assert keys == {'email_address', 'creation_time', 'verified'}


@pytest.mark.asyncio
async def test_fetching_existing_user_with_invalid_access_token(
        client,
        account_data,
        username,
        cleanup,
    ):
    """Test that correct account data is returned on valid request."""
    await main.account_manager.create(username, account_data)
    access_token = access.generate('tomato')['access_token']
    headers = {'Authorization': f'Bearer {access_token}'}
    response = await client.get(f'/users/{username}', headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_fetching_nonexistent_user(client, headers, username):
    """Test that correct account data is returned on valid request."""
    response = await client.get(f'/users/{username}', headers=headers)
    assert response.status_code == 404


################################################################################
# Create User
################################################################################


@pytest.mark.asyncio
async def test_creating_user_with_valid_account_data(
        client,
        account_datas,
        cleanup,
    ):
    """Test that account is created successfully on valid request."""
    account_data = account_datas['valid'][1]
    username = account_data['username']
    response = await client.post(url=f'/users/{username}', json=account_data)
    assert response.status_code == 200
    entry = await database.database['accounts'].find_one({'_id': username})
    assert entry is not None


@pytest.mark.asyncio
async def test_creating_user_with_invalid_account_data(client, account_datas):
    """Test that account creation fails when given invalid account data."""
    account_data = account_datas['invalid'][0]
    username = account_data['username']
    response = await client.post(url=f'/users/{username}', json=account_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'invalid account data'
    entry = await database.database['accounts'].find_one({'_id': username})
    assert entry is None


@pytest.mark.asyncio
async def test_creating_user_username_already_taken(
        client,
        username,
        email_address,
        account_data,
    ):
    """Test that account creation fails when the username is already taken."""
    account_data = copy.deepcopy(account_data)
    account_data['email_address'] = 'tomato@fastsurvey.de'
    response = await client.post(url=f'/users/{username}', json=account_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'username already taken'
    entry = await database.database['accounts'].find_one({'_id': username})
    assert entry['email_address'] == email_address


@pytest.mark.asyncio
async def test_creating_user_email_address_already_taken(
        client,
        username,
        email_address,
        account_data,
    ):
    """Test that account creation fails when the email address is in use."""
    account_data = copy.deepcopy(account_data)
    account_data['username'] = 'tomato'
    response = await client.post(url='/users/tomato', json=account_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'email address already taken'
    entry = await database.database['accounts'].find_one(
        filter={'email_address': email_address},
    )
    assert entry['_id'] == username


# TODO update user
# TODO delete user
# TODO fetch surveys


################################################################################
# Fetch Survey
################################################################################


# TODO compare get request with caching and without caching


@pytest.mark.asyncio
async def test_fetching_existing_survey(client, username, configurationss):
    """Test that correct configuration is returned for an existing survey."""
    for survey_name, configurations in configurationss.items():
        response = await client.get(f'/users/{username}/surveys/{survey_name}')
        assert response.status_code == 200
        assert response.json() == configurations['valid']


@pytest.mark.asyncio
async def test_fetching_nonexistent_survey(client, username):
    """Test that exception is raised when requesting a nonexistent survey."""
    response = await client.get(f'/users/{username}/surveys/tomato')
    assert response.status_code == 404
    assert response.json()['detail'] == 'survey not found'


@pytest.mark.asyncio
async def test_fetching_survey_in_draft_mode(
        client,
        headers,
        username,
        configurationss,
        cleanup,
    ):
    """Test that exception is raised when requesting a survey in draft mode."""
    configuration = copy.deepcopy(configurationss['complex']['valid'])
    survey_name = 'tomato'
    configuration['survey_name'] = survey_name
    configuration['draft'] = True
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    response = await client.get(f'/users/{username}/surveys/{survey_name}')
    assert response.status_code == 404
    assert response.json()['detail'] == 'survey not found'


################################################################################
# Create Survey
################################################################################


@pytest.mark.asyncio
async def test_creating_survey_with_valid_configuration(
        client,
        headers,
        username,
        configurationss,
        cleanup,
    ):
    """Test that survey is correctly created with a valid configuration."""
    configuration = copy.deepcopy(configurationss['complex']['valid'])
    survey_name = 'tomato'
    configuration['survey_name'] = survey_name
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert response.status_code == 200
    assert main.survey_manager.cache.fetch(username, survey_name) is not None
    entry = await database.database['configurations'].find_one(
        filter={'username': username, 'survey_name': survey_name},
    )
    assert entry is not None


@pytest.mark.asyncio
async def test_creating_survey_with_invalid_configuration(
        client,
        headers,
        username,
        configurationss,
    ):
    """Test that survey creation fails with an invalid configuration."""
    configuration = copy.deepcopy(configurationss['complex']['invalid'][0])
    survey_name = 'tomato'
    configuration['survey_name'] = survey_name
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'invalid configuration'
    with pytest.raises(KeyError):
        main.survey_manager.cache.fetch(username, survey_name)
    entry = await database.database['configurations'].find_one(
        filter={'username': username, 'survey_name': survey_name},
    )
    assert entry is None


# TODO update survey
# TODO reset survey
# TODO delete survey


################################################################################
# Create Submission
#
# It suffices here to test only one valid and one invalid submission, instead
# of all examples that we have, as the validation is tested on its own.
# Additionally, that gets us a pretty nice speed-up.
################################################################################


@pytest.mark.asyncio
async def test_creating_valid_submission(
        client,
        username,
        submissionss,
        cleanup,
    ):
    """Test that submission works with valid submissions for test surveys."""
    survey_name = 'complex'
    submission = submissionss[survey_name]['valid'][0]
    survey = await main.survey_manager.fetch(username, survey_name)
    url = f'/users/{username}/surveys/{survey_name}/submissions'
    response = await client.post(url, json=submission)
    assert response.status_code == 200
    entry = await survey.submissions.find_one({'data': submission})
    assert entry is not None


@pytest.mark.asyncio
async def test_creating_invalid_submission(
        client,
        username,
        submissionss,
        cleanup,
    ):
    """Test that submit correctly fails for invalid test survey submissions."""
    survey_name = 'complex'
    submission = submissionss[survey_name]['invalid'][0]
    survey = await main.survey_manager.fetch(username, survey_name)
    url = f'/users/{username}/surveys/{survey_name}/submissions'
    response = await client.post(url, json=submission)
    assert response.status_code == 400
    entry = await survey.submissions.find_one()
    assert entry is None


################################################################################
# Verify submission
################################################################################


# TODO go through tests, don't skip any


@pytest.mark.skip(reason='scheduled for refactoring')
@pytest.mark.asyncio
async def test_duplicate_validation_token_resolution(
        monkeypatch,
        client,
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

    for i, submission in enumerate(submissions):
        response = await client.post(
            url=f'/users/{username}/surveys/{survey_name}/submissions',
            json=submission,
        )
        assert response.status_code == 200
        entry = await survey.submissions.find_one({'data': submission})
        assert entry is not None
        assert entry['_id'] == str(i)


@pytest.mark.skip(reason='scheduled for refactoring')
@pytest.mark.asyncio
async def test_verifying_valid_token(
        monkeypatch,
        client,
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

    base_url = f'/users/{username}/surveys/{survey_name}'
    for submission in submissions:
        await client.post(f'{base_url}/submission', json=submission)
    for i, token in enumerate(tokens):
        response = await client.get(
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


################################################################################
# Fetch Results
################################################################################


# TODO needs more tests


@pytest.mark.asyncio
async def test_fetching_results(
        client,
        headers,
        username,
        submissionss,
        resultss,
        cleanup,
    ):
    """Test that aggregation of test submissions returns the correct result."""
    for survey_name, submissions in submissionss.items():
        # push test submissions
        survey = await main.survey_manager.fetch(username, survey_name)
        await survey.alligator.collection.insert_many([
            {'data': submission}
            for submission
            in submissions['valid']
        ])
        # manually close (cached) survey so that we can aggregate
        survey.end = 0
        # aggregate and fetch results
        url = f'/users/{username}/surveys/{survey_name}/results'
        response = await client.get(url=url, headers=headers)
        assert response.status_code == 200
        assert response.json() == resultss[survey_name]


################################################################################
# Decode Access Token
#
# We don't really need to test much more here, the decoding route is a direct
# function call to access.decode which is in itself sufficiently tested.
################################################################################


@pytest.mark.asyncio
async def test_decoding_valid_access_token(client, username, headers):
    """Test that the correct username is returned for a valid access token."""
    response = await client.get(f'/authentication', headers=headers)
    assert response.status_code == 200
    assert response.json() == username


################################################################################
# Generate Access Token
################################################################################


@pytest.mark.asyncio
async def test_generating_access_token_with_non_verified_account(
        client,
        username,
        password,
    ):
    """Test that authentication fails when the account is not verified."""
    credentials = dict(identifier=username, password=password)
    response = await client.post(f'/authentication', json=credentials)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_generating_access_token_with_valid_credentials(
        client,
        username,
        email_address,
        password,
        cleanup,
    ):
    """Test that authentication works with valid identifier and password."""
    await database.database['accounts'].update_one(
        filter={'_id': username},
        update={'$set': {'verified': True}}
    )
    # test with username as well as email address as identifier
    for identifier in [username, email_address]:
        credentials = dict(
            identifier=identifier,
            password=password,
        )
        response = await client.post(f'/authentication', json=credentials)
        assert response.status_code == 200
        assert access.decode(response.json()['access_token']) == username


@pytest.mark.asyncio
async def test_generating_access_token_invalid_username(
        client,
        username,
    ):
    """Test that authentication fails for a user that does not exist."""
    credentials = dict(identifier='tomato', password='tomato')
    response = await client.post(f'/authentication', json=credentials)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generating_access_token_with_invalid_password(
        client,
        username,
        cleanup,
    ):
    """Test that authentication fails given an incorrect password."""
    await database.database['accounts'].update_one(
        filter={'_id': username},
        update={'$set': {'verified': True}}
    )
    credentials = dict(
        identifier=username,
        password='tomato',
    )
    response = await client.post(f'/authentication', json=credentials)
    assert response.status_code == 401


################################################################################
# Refresh Access Token
#
# We don't really need to test much more here, the refresh route is composed
# of direct function calls to the access model which is in itself sufficiently
# tested.
################################################################################


@pytest.mark.asyncio
async def test_refreshing_valid_access_token(client, username, headers):
    """Test that the correct username is returned for a valid access token."""
    response = await client.put(f'/authentication', headers=headers)
    assert response.status_code == 200
    assert access.decode(response.json()['access_token']) == username


################################################################################
# Verify Email Address
################################################################################


@pytest.mark.asyncio
async def test_verifying_email_address_with_valid_credentials(
        client,
        username,
        password,
        cleanup,
    ):
    """Test that email verification works given valid credentials."""
    account_data = await database.database['accounts'].find_one(
        filter={'_id': username},
        projection={'_id': False, 'verification_token': True},
    )
    credentials = dict(
        verification_token=account_data['verification_token'],
        password=password,
    )
    response = await client.post(f'/verification', json=credentials)
    assert response.status_code == 200
    assert access.decode(response.json()['access_token']) == username
    account_data = await database.database['accounts'].find_one(
        filter={'_id': username},
        projection={'_id': False, 'verified': True},
    )
    assert account_data['verified']


@pytest.mark.asyncio
async def test_verifying_email_address_with_invalid_verification_token(
        client,
        username,
    ):
    """Test that email verification fails with invalid verification token."""
    credentials = dict(verification_token='tomato', password='tomato')
    response = await client.post(f'/verification', json=credentials)
    assert response.status_code == 401
    account_data = await database.database['accounts'].find_one(
        filter={'_id': username},
        projection={'_id': False, 'verified': True},
    )
    assert not account_data['verified']


@pytest.mark.asyncio
async def test_verifying_email_address_with_invalid_password(
        client,
        username,
    ):
    """Test that email verification fails given an invalid password."""
    account_data = await database.database['accounts'].find_one(
        filter={'_id': username},
        projection={'_id': False, 'verification_token': True},
    )
    credentials = dict(
        verification_token=account_data['verification_token'],
        password='tomato',
    )
    response = await client.post(f'/verification', json=credentials)
    assert response.status_code == 401
    account_data = await database.database['accounts'].find_one(
        filter={'_id': username},
        projection={'_id': False, 'verified': True},
    )
    assert not account_data['verified']


@pytest.mark.asyncio
async def test_verifying_previously_verified_email_address(
        client,
        username,
        password,
        cleanup,
    ):
    """Test that email verification works given valid credentials."""
    await database.database['accounts'].update_one(
        filter={'_id': username},
        update={'$set': {'verified': True}}
    )
    account_data = await database.database['accounts'].find_one(
        filter={'_id': username},
        projection={'_id': False, 'verification_token': True},
    )
    credentials = dict(
        verification_token=account_data['verification_token'],
        password=password,
    )
    response = await client.post(f'/verification', json=credentials)
    assert response.status_code == 400
    account_data = await database.database['accounts'].find_one(
        filter={'_id': username},
        projection={'_id': False, 'verified': True},
    )
    assert account_data['verified']
