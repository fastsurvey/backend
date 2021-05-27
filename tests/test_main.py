import pytest
import secrets
import httpx
import copy

import app.main as main
import app.resources.database as database
import app.cryptography.access as access
import app.cryptography.verification as verification


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
        username,
        account_data,
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
        username,
        account_data,
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
        username,
        account_data,
        cleanup,
    ):
    """Test that account is created successfully on valid request."""
    response = await client.post(url=f'/users/{username}', json=account_data)
    assert response.status_code == 200
    entry = await database.database['accounts'].find_one({})
    assert entry['_id'] == username


@pytest.mark.asyncio
async def test_creating_user_with_invalid_account_data(client, account_datas):
    """Test that account creation fails when given invalid account data."""
    account_data = account_datas['invalid'][0]
    username = account_data['username']
    response = await client.post(url=f'/users/{username}', json=account_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'invalid account data'
    entry = await database.database['accounts'].find_one({})
    assert entry is None


@pytest.mark.asyncio
async def test_creating_user_username_already_taken(
        client,
        username,
        email_address,
        account_data,
        cleanup,
    ):
    """Test that account creation fails when the username is already taken."""
    await client.post(url=f'/users/{username}', json=account_data)
    account_data = copy.deepcopy(account_data)
    account_data['email_address'] = 'test@fastsurvey.de'
    response = await client.post(url=f'/users/{username}', json=account_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'username already taken'
    entry = await database.database['accounts'].find_one({})
    assert entry['email_address'] == email_address


@pytest.mark.asyncio
async def test_creating_user_email_address_already_taken(
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that account creation fails when the email address is in use."""
    await client.post(url=f'/users/{username}', json=account_data)
    account_data = copy.deepcopy(account_data)
    account_data['username'] = 'tomato'
    response = await client.post(url='/users/tomato', json=account_data)
    assert response.status_code == 400
    assert response.json()['detail'] == 'email address already taken'
    entry = await database.database['accounts'].find_one({})
    assert entry['_id'] == username


# TODO update user
# TODO delete user
# TODO fetch surveys


################################################################################
# Fetch Survey
################################################################################


@pytest.mark.asyncio
async def test_fetching_existing_survey(
        client,
        headers,
        username,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that correct configuration is returned for an existing survey."""
    await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    # reset cache in order to test fetching with cache miss
    main.survey_manager.cache.reset()
    response = await client.get(f'/users/{username}/surveys/{survey_name}')
    assert response.status_code == 200
    assert response.json() == configuration


@pytest.mark.asyncio
async def test_fetching_nonexistent_survey(client, username):
    """Test that exception is raised when requesting a nonexistent survey."""
    response = await client.get(f'/users/{username}/surveys/complex')
    assert response.status_code == 404
    assert response.json()['detail'] == 'survey not found'


@pytest.mark.asyncio
async def test_fetching_survey_in_draft_mode(
        client,
        headers,
        username,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that exception is raised when requesting a survey in draft mode."""
    configuration = copy.deepcopy(configuration)
    configuration['draft'] = True
    await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    # reset cache in order to test fetching with cache miss
    main.survey_manager.cache.reset()
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
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey is correctly created given a valid configuration."""
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert response.status_code == 200
    assert main.survey_manager.cache.fetch(username, survey_name)
    entry = await database.database['configurations'].find_one({})
    assert entry['username'] == username
    assert entry['survey_name'] == survey_name


@pytest.mark.asyncio
async def test_creating_survey_with_invalid_configuration(
        client,
        headers,
        username,
        survey_name,
        configurationss,
    ):
    """Test that survey creation fails with an invalid configuration."""
    configuration = configurationss[survey_name]['invalid'][0]
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert response.status_code == 400
    assert response.json()['detail'] == 'invalid configuration'
    with pytest.raises(KeyError):
        main.survey_manager.cache.fetch(username, survey_name)
    entry = await database.database['configurations'].find_one({})
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
        headers,
        username,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that submission works given a valid submission."""
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    survey = await main.survey_manager.fetch(username, survey_name)
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}/submissions',
        json=submissions[0],
    )
    assert response.status_code == 200
    entry = await survey.submissions.find_one({})
    assert entry['data'] == submissions[0]


@pytest.mark.asyncio
async def test_creating_invalid_submission(
        client,
        headers,
        username,
        survey_name,
        configuration,
        submissionss,
        cleanup,
    ):
    """Test that submit correctly fails given an invalid submissions."""
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    survey = await main.survey_manager.fetch(username, survey_name)
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}/submissions',
        json=submissionss[survey_name]['invalid'][0],
    )
    assert response.status_code == 400
    entry = await survey.submissions.find_one({})
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


# TODO test all aggregations in test_aggregation + more tests


@pytest.mark.asyncio
async def test_fetching_results(
        monkeypatch,
        client,
        headers,
        username,
        survey_name,
        configuration,
        submissions,
        results,
        cleanup,
    ):
    """Test that aggregation of test submissions returns the correct result."""
    await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    # mock verification token generation
    tokens = []

    def token():
        tokens.append(str(len(tokens)))
        return tokens[-1]

    monkeypatch.setattr(verification, 'token', token)
    # push test submissions
    for submission in submissions:
        await client.post(
            url=f'/users/{username}/surveys/{survey_name}/submissions',
            json=submission,
        )
    # validate the submissions
    for x in tokens:
        await client.get(
            url=f'/users/{username}/surveys/{survey_name}/verification/{x}',
            allow_redirects=False,
        )
    # close survey so that we can aggregate
    configuration = copy.deepcopy(configuration)
    configuration['end'] = 0
    await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    # aggregate and fetch results
    response = await client.get(
        url=f'/users/{username}/surveys/{survey_name}/results',
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == results


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
        account_data,
        cleanup,
    ):
    """Test that authentication fails when the account is not verified."""
    await client.post(url=f'/users/{username}', json=account_data)
    credentials = dict(identifier=username, password=password)
    response = await client.post(f'/authentication', json=credentials)
    assert response.status_code == 400
    assert response.json()['detail'] == 'account not verified'


@pytest.mark.asyncio
async def test_generating_access_token_with_valid_credentials(
        monkeypatch,
        client,
        username,
        email_address,
        password,
        account_data,
        cleanup,
    ):
    """Test that authentication works with valid identifier and password."""


    # mock verification token generation
    tokens = []

    def token():
        tokens.append(str(len(tokens)))
        return tokens[-1]

    monkeypatch.setattr(verification, 'token', token)


    await client.post(url=f'/users/{username}', json=account_data)
    await client.post(
        url=f'/verification',
        json={'verification_token': tokens[0], 'password': password},
    )

    # test with username as well as email address as identifier
    for identifier in [username, email_address]:
        response = await client.post(
            url='/authentication',
            json={'identifier': identifier, 'password': password},
        )
        assert response.status_code == 200
        assert access.decode(response.json()['access_token']) == username


@pytest.mark.asyncio
async def test_generating_access_token_invalid_username(
        monkeypatch,
        client,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that authentication fails for a user that does not exist."""


    # mock verification token generation
    tokens = []

    def token():
        tokens.append(str(len(tokens)))
        return tokens[-1]

    monkeypatch.setattr(verification, 'token', token)


    await client.post(url=f'/users/{username}', json=account_data)
    await client.post(
        url=f'/verification',
        json={'verification_token': tokens[0], 'password': password},
    )
    credentials = dict(identifier='tomato', password=password)
    response = await client.post(url='/authentication', json=credentials)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generating_access_token_with_invalid_password(
        monkeypatch,
        client,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that authentication fails given an incorrect password."""


    # mock verification token generation
    tokens = []

    def token():
        tokens.append(str(len(tokens)))
        return tokens[-1]

    monkeypatch.setattr(verification, 'token', token)


    await client.post(url=f'/users/{username}', json=account_data)
    await client.post(
        url=f'/verification',
        json={'verification_token': tokens[0], 'password': password},
    )
    credentials = dict(identifier=username, password='tomato')
    response = await client.post(url='/authentication', json=credentials)
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
        monkeypatch,
        client,
        headers,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that email verification works given valid credentials."""


    # mock verification token generation
    tokens = []

    def token():
        tokens.append(str(len(tokens)))
        return tokens[-1]

    monkeypatch.setattr(verification, 'token', token)


    await client.post(url=f'/users/{username}', json=account_data)
    response = await client.post(
        url=f'/verification',
        json={'verification_token': tokens[0], 'password': password},
    )
    assert response.status_code == 200
    assert access.decode(response.json()['access_token']) == username
    response = await client.get(f'/users/{username}', headers=headers)
    assert response.json()['verified']


@pytest.mark.asyncio
async def test_verifying_email_address_with_invalid_verification_token(
        client,
        headers,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that email verification fails with invalid verification token."""
    await client.post(url=f'/users/{username}', json=account_data)
    response = await client.post(
        url=f'/verification',
        json={'verification_token': 'tomato', 'password': password},
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'invalid verification token'
    response = await client.get(f'/users/{username}', headers=headers)
    assert not response.json()['verified']


@pytest.mark.asyncio
async def test_verifying_email_address_with_invalid_password(
        monkeypatch,
        client,
        headers,
        username,
        account_data,
        cleanup,
    ):
    """Test that email verification fails given an invalid password."""


    # mock verification token generation
    tokens = []

    def token():
        tokens.append(str(len(tokens)))
        return tokens[-1]

    monkeypatch.setattr(verification, 'token', token)


    await client.post(url=f'/users/{username}', json=account_data)
    response = await client.post(
        url=f'/verification',
        json={'verification_token': tokens[0], 'password': 'tomato'},
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'invalid password'
    response = await client.get(f'/users/{username}', headers=headers)
    assert not response.json()['verified']


@pytest.mark.asyncio
async def test_verifying_previously_verified_email_address(
        monkeypatch,
        client,
        headers,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that email verification works given valid credentials."""


    # mock verification token generation
    tokens = []

    def token():
        tokens.append(str(len(tokens)))
        return tokens[-1]

    monkeypatch.setattr(verification, 'token', token)


    await client.post(url=f'/users/{username}', json=account_data)
    credentials = {'verification_token': tokens[0], 'password': password}
    await client.post(url='/verification', json=credentials)
    response = await client.post(url='/verification', json=credentials)
    assert response.status_code == 400
    assert response.json()['detail'] == 'account already verified'
    response = await client.get(f'/users/{username}', headers=headers)
    assert response.json()['verified']
