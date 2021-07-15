import pytest
import secrets
import httpx
import copy

import app.main as main
import app.resources.database as database
import app.cryptography.access as access
import app.cryptography.password as pw
import app.errors as errors


@pytest.fixture(scope='module')
async def client():
    """Provide a HTTPX AsyncClient that is properly closed after testing."""
    client = httpx.AsyncClient(
        app=main.app,
        base_url='http://example.com',
    )
    yield client
    await client.aclose()


def check_error(response, error):
    """Check that a HTTPX request returned with a specific error."""
    return (
        response.status_code == error.STATUS_CODE
        and response.json()['detail'] == error.DETAIL
    )


################################################################################
# Fetch User
################################################################################


@pytest.mark.asyncio
async def test_fetching_existing_user_with_valid_access_token(
        mock_email_sending,
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
        mock_email_sending,
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
    assert check_error(response, errors.AccessForbiddenError)


@pytest.mark.asyncio
async def test_fetching_nonexistent_user(client, headers, username):
    """Test that correct account data is returned on valid request."""
    response = await client.get(f'/users/{username}', headers=headers)
    assert check_error(response, errors.UserNotFoundError)


################################################################################
# Create User
################################################################################


@pytest.mark.asyncio
async def test_creating_user_with_valid_account_data(
        mock_email_sending,
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
    assert check_error(response, errors.InvalidAccountDataError)
    entry = await database.database['accounts'].find_one({})
    assert entry is None


@pytest.mark.asyncio
async def test_creating_user_username_already_taken(
        mock_email_sending,
        client,
        username,
        email_address,
        account_data,
        account_datas,
        cleanup,
    ):
    """Test that account creation fails when the username is already taken."""
    await client.post(url=f'/users/{username}', json=account_data)
    account_data_duplicate = copy.deepcopy(account_datas['valid'][1])
    account_data_duplicate['username'] = username
    response = await client.post(
        url=f'/users/{account_data_duplicate["username"]}',
        json=account_data_duplicate,
    )
    assert check_error(response, errors.UsernameAlreadyTakenError)
    entry = await database.database['accounts'].find_one({})
    assert entry['email_address'] == email_address


@pytest.mark.asyncio
async def test_creating_user_email_address_already_taken(
        mock_email_sending,
        client,
        username,
        email_address,
        account_data,
        account_datas,
        cleanup,
    ):
    """Test that account creation fails when the email address is in use."""
    await client.post(url=f'/users/{username}', json=account_data)
    account_data_duplicate = copy.deepcopy(account_datas['valid'][1])
    account_data_duplicate['email_address'] = email_address
    response = await client.post(
        url=f'/users/{account_data_duplicate["username"]}',
        json=account_data_duplicate,
    )
    assert check_error(response, errors.EmailAddressAlreadyTakenError)
    entry = await database.database['accounts'].find_one({})
    assert entry['_id'] == username


################################################################################
# Update User
################################################################################


# TODO test_updating_existing_user_with_valid_username_not_in_use
# TODO test_updating_existent_user_with_valid_username_in_use
# TODO test_updating_existing_user_with_valid_email_address_not_in_use

# TODO test_updating_nonexistent_user_with_valid_account_data
# this should return a 401, not a 404, we need to implement that an access
# token is useless when the user is deleted/does not exist for this


@pytest.mark.asyncio
async def test_updating_existing_user_with_no_changes(
        mock_email_sending,
        client,
        headers,
        username,
        account_data,
        cleanup,
):
    """Test that account is correctly updated given valid account data."""
    await client.post(url=f'/users/{username}', json=account_data)
    entry = await database.database['accounts'].find_one({})
    response = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert response.status_code == 200
    assert entry == await database.database['accounts'].find_one({})


@pytest.mark.asyncio
async def test_updating_existing_user_with_valid_password(
        mock_email_sending,
        client,
        headers,
        username,
        account_data,
        account_datas,
        cleanup,
):
    """Test that account is correctly updated given valid account data."""
    await client.post(url=f'/users/{username}', json=account_data)
    account_data = copy.deepcopy(account_data)
    account_data['password'] = account_datas['valid'][1]['password']
    response = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert response.status_code == 200
    entry = await database.database['accounts'].find_one({})
    assert pw.verify(
        password=account_datas['valid'][1]['password'],
        password_hash=entry['password_hash'],
    )


@pytest.mark.skip(reason='todo')
@pytest.mark.asyncio
async def test_updating_existing_user_with_valid_email_address_in_use(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        account_data,
        account_datas,
        cleanup,
):
    """Test that updating the email address to one in use fails correctly."""
    for i, acc in enumerate(account_datas['valid'][:2]):
        await client.post(url=f'/users/{acc["username"]}', json=acc)
        credentials = dict(verification_token=str(i), password=acc['password'])
        await client.post(url='/verification', json=credentials)
    account_data = copy.deepcopy(account_data)
    account_data['email_address'] = account_datas['valid'][1]['email_address']
    response = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert check_error(response, errors.EmailAddressAlreadyTakenError)


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
    assert check_error(response, errors.SurveyNotFoundError)


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
    assert check_error(response, errors.SurveyNotFoundError)


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
    assert check_error(response, errors.InvalidConfigurationError)
    with pytest.raises(KeyError):
        main.survey_manager.cache.fetch(username, survey_name)
    entry = await database.database['configurations'].find_one({})
    assert entry is None


################################################################################
# Update Survey
################################################################################


@pytest.mark.asyncio
async def test_updating_existing_survey_with_valid_configuration(
        client,
        headers,
        username,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey is correctly updated given a valid configuration."""
    await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    configuration = copy.deepcopy(configuration)
    configuration['description'] = 'Hello World!'
    response = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert response.status_code == 200
    survey = main.survey_manager.cache.fetch(username, survey_name)
    assert survey.configuration['description'] == configuration['description']
    entry = await database.database['configurations'].find_one({})
    assert entry['description'] == configuration['description']


@pytest.mark.asyncio
async def test_updating_nonexistent_survey_with_valid_configuration(
        client,
        headers,
        username,
        survey_name,
        configuration,
    ):
    """Test that survey update fails when the survey does not exist."""
    response = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert check_error(response, errors.SurveyNotFoundError)
    with pytest.raises(KeyError):
        main.survey_manager.cache.fetch(username, survey_name)
    entry = await database.database['configurations'].find_one({})
    assert entry is None


@pytest.mark.asyncio
async def test_updating_survey_name_to_survey_name_not_in_use(
        client,
        headers,
        username,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey name is updated when it is not already used."""
    await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    configuration = copy.deepcopy(configuration)
    configuration['survey_name'] = 'tomato'
    response = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert response.status_code == 200
    assert main.survey_manager.cache.fetch(username, 'tomato')
    entry = await database.database['configurations'].find_one({})
    assert entry['survey_name'] == 'tomato'


@pytest.mark.asyncio
async def test_updating_survey_name_to_survey_name_in_use(
        client,
        headers,
        username,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey name update fails if survey name is already in use."""
    await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    configuration = copy.deepcopy(configuration)
    configuration['survey_name'] = 'tomato'
    await client.post(
        url=f'/users/{username}/surveys/tomato',
        headers=headers,
        json=configuration,
    )
    response = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert check_error(response, errors.SurveyNameAlreadyTakenError)
    assert main.survey_manager.cache.fetch(username, survey_name)
    entry = await database.database['configurations'].find_one(
        filter={'survey_name': survey_name},
    )
    assert entry is not None


# TODO reset survey
# TODO delete survey


################################################################################
# Create Submission
#
# It suffices here to test only one valid and one invalid submission, instead
# of all examples that we have, as the validation is tested on its own.
################################################################################


@pytest.mark.asyncio
async def test_creating_valid_submission(
        mock_email_sending,
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
    entry = await survey.unverified_submissions.find_one({})
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
    assert check_error(response, errors.InvalidSubmissionError)
    entry = await survey.unverified_submissions.find_one({})
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


@pytest.mark.asyncio
async def test_fetching_results(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        configurationss,
        submissionss,
        resultss,
        cleanup,
    ):
    """Test that aggregating test submissions returns the correct result."""
    counter = 0
    for survey_name, configurations in configurationss.items():
        path = f'/users/{username}/surveys/{survey_name}'
        await client.post(
            url=path,
            headers=headers,
            json=configurations['valid'],
        )
        # push test submissions and validate them
        for submission in submissionss[survey_name]['valid']:
            await client.post(url=f'{path}/submissions', json=submission)
            if configurations['valid']['authentication'] != 'open':
                await client.get(
                    url=f'{path}/verification/{counter}',
                    allow_redirects=False,
                )
                counter += 1
        # aggregate and fetch results
        response = await client.get(url=f'{path}/results', headers=headers)
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
        mock_email_sending,
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
    assert check_error(response, errors.AccountNotVerifiedError)


@pytest.mark.asyncio
async def test_generating_access_token_with_valid_credentials(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        username,
        email_address,
        password,
        account_data,
        cleanup,
    ):
    """Test that authentication works with valid identifier and password."""
    await client.post(url=f'/users/{username}', json=account_data)
    await client.post(
        url=f'/verification',
        json={'verification_token': '0', 'password': password},
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
        mock_email_sending,
        mock_verification_token_generation,
        client,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that authentication fails for a user that does not exist."""
    await client.post(url=f'/users/{username}', json=account_data)
    await client.post(
        url=f'/verification',
        json={'verification_token': '0', 'password': password},
    )
    credentials = dict(identifier='tomato', password=password)
    response = await client.post(url='/authentication', json=credentials)
    assert check_error(response, errors.UserNotFoundError)


@pytest.mark.asyncio
async def test_generating_access_token_with_invalid_password(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that authentication fails given an incorrect password."""
    await client.post(url=f'/users/{username}', json=account_data)
    await client.post(
        url=f'/verification',
        json={'verification_token': '0', 'password': password},
    )
    credentials = dict(identifier=username, password='tomato')
    response = await client.post(url='/authentication', json=credentials)
    assert check_error(response, errors.InvalidPasswordError)


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
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that email verification works given valid credentials."""
    await client.post(url=f'/users/{username}', json=account_data)
    response = await client.post(
        url=f'/verification',
        json={'verification_token': '0', 'password': password},
    )
    assert response.status_code == 200
    assert access.decode(response.json()['access_token']) == username
    response = await client.get(f'/users/{username}', headers=headers)
    assert response.json()['verified']


@pytest.mark.asyncio
async def test_verifying_email_address_with_invalid_verification_token(
        mock_email_sending,
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
    assert check_error(response, errors.InvalidVerificationTokenError)
    response = await client.get(f'/users/{username}', headers=headers)
    assert not response.json()['verified']


@pytest.mark.asyncio
async def test_verifying_email_address_with_invalid_password(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        account_data,
        cleanup,
    ):
    """Test that email verification fails given an invalid password."""
    await client.post(url=f'/users/{username}', json=account_data)
    response = await client.post(
        url=f'/verification',
        json={'verification_token': '0', 'password': 'tomato'},
    )
    assert check_error(response, errors.InvalidPasswordError)
    response = await client.get(f'/users/{username}', headers=headers)
    assert not response.json()['verified']


@pytest.mark.asyncio
async def test_verifying_previously_verified_email_address(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that email verification works given valid credentials."""
    await client.post(url=f'/users/{username}', json=account_data)
    credentials = {'verification_token': '0', 'password': password}
    await client.post(url='/verification', json=credentials)
    response = await client.post(url='/verification', json=credentials)
    assert check_error(response, errors.InvalidVerificationTokenError)
    response = await client.get(f'/users/{username}', headers=headers)
    assert response.json()['verified']
