import pytest
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
    client = httpx.AsyncClient(app=main.app, base_url='http://example.com')
    yield client
    await client.aclose()


def check_error(response, error):
    """Check that a HTTPX request returned with a specific error."""
    if error is None:
        return response.status_code == 422
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
    await client.post(f'/users/{username}', json=account_data)
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
    await client.post(f'/users/{username}', json=account_data)
    access_token = access.generate('kangaroo')['access_token']
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
async def test_creating_user_with_invalid_account_data(
        client,
        invalid_account_datas,
    ):
    """Test that account creation fails when given invalid account data."""
    account_data = invalid_account_datas[0]
    username = account_data['username']
    response = await client.post(url=f'/users/{username}', json=account_data)
    assert check_error(response, None)
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
    account_data_duplicate = copy.deepcopy(account_datas[1])
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
    account_data_duplicate = copy.deepcopy(account_datas[1])
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
    account_data['password'] = account_datas[1]['password']
    response = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert response.status_code == 200
    entry = await database.database['accounts'].find_one({})
    assert pw.verify(
        password=account_datas[1]['password'],
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
        verification_credentials = dict(
            verification_token=str(i).zfill(64),
            password=acc['password'],
        )
        await client.post(url='/verification', json=verification_credentials)
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
        invalid_configurationss,
    ):
    """Test that survey creation fails with an invalid configuration."""
    configuration = invalid_configurationss[survey_name][0]
    response = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert check_error(response, None)
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
    configuration['survey_name'] = 'kangaroo'
    response = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert response.status_code == 200
    assert main.survey_manager.cache.fetch(username, 'kangaroo')
    entry = await database.database['configurations'].find_one({})
    assert entry['survey_name'] == 'kangaroo'


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
    configuration['survey_name'] = 'kangaroo'
    await client.post(
        url=f'/users/{username}/surveys/kangaroo',
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


@pytest.mark.asyncio
async def test_updating_survey_with_existing_submissions(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that survey name update fails if it has existing submissions."""
    path = f'/users/{username}/surveys/{survey_name}'
    await client.post(url=path, headers=headers, json=configuration)
    # push and validate a submission
    await client.post(url=f'{path}/submissions', json=submissions[0])
    await client.get(
        url=f'{path}/verification/{str(0).zfill(64)}',
        allow_redirects=False,
    )
    # push changed configuration
    configuration = copy.deepcopy(configuration)
    configuration['description'] = 'chameleon'
    response = await client.put(url=path, headers=headers, json=configuration)
    # check validity
    assert check_error(response, errors.SubmissionsExistError)
    survey = main.survey_manager.cache.fetch(username, survey_name)
    assert survey.configuration['description'] != configuration['description']
    entry = await database.database['configurations'].find_one({})
    assert entry['description'] != configuration['description']


# TODO reset survey
# TODO delete survey


################################################################################
# Create Submission
#
# It suffices here to test only one valid and one invalid submission, instead
# of all examples that we have, as the validation is tested on its own.
################################################################################


@pytest.mark.asyncio
async def test_creating_submission(
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
    path = f'/users/{username}/surveys/{survey_name}'
    await client.post(url=path, headers=headers, json=configuration)
    survey = await main.survey_manager.fetch(username, survey_name)
    response = await client.post(url=f'{path}/submissions', json=submissions[0])
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
        invalid_submissionss,
        cleanup,
    ):
    """Test that submit correctly fails given an invalid submissions."""
    path = f'/users/{username}/surveys/{survey_name}'
    await client.post(url=path, headers=headers, json=configuration)
    survey = await main.survey_manager.fetch(username, survey_name)
    response = await client.post(
        url=f'{path}/submissions',
        json=invalid_submissionss[survey_name][0],
    )
    assert check_error(response, None)
    entry = await survey.unverified_submissions.find_one({})
    assert entry is None


@pytest.mark.asyncio
async def test_creating_submission_with_submission_limit_reached(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that submission is rejected when submission limit is reached."""
    path = f'/users/{username}/surveys/{survey_name}'
    # push survey that has a limit of a single submission
    configuration = copy.deepcopy(configuration)
    configuration['limit'] = 1
    await client.post(url=path, headers=headers, json=configuration)
    # push and validate a submission
    await client.post(url=f'{path}/submissions', json=submissions[0])
    await client.get(
        url=f'{path}/verification/{str(0).zfill(64)}',
        allow_redirects=False,
    )
    # push a second submission and verify
    response = await client.post(url=f'{path}/submissions', json=submissions[0])
    assert check_error(response, errors.SubmissionLimitReachedError)
    survey = main.survey_manager.cache.fetch(username, survey_name)
    x = await survey.submissions.find_one({})
    assert x['data'] == submissions[0]


################################################################################
# Verify submission
################################################################################


@pytest.mark.asyncio
async def test_verifying_valid_verification_token(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test submission is correctly verified given valid verification token."""
    path = f'/users/{username}/surveys/{survey_name}'
    await client.post(url=path, headers=headers, json=configuration)
    await client.post(url=f'{path}/submissions', json=submissions[0])
    verification_token = str(0).zfill(64)
    response = await client.get(
        url=f'{path}/verification/{verification_token}',
        allow_redirects=False,
    )
    assert response.status_code == 307
    survey = await main.survey_manager.fetch(username, survey_name)
    e = await survey.unverified_submissions.find_one(
        filter={'_id': verification_token},
    )
    assert e is not None  # still unchanged in unverified submissions
    e = await survey.submissions.find_one(
        filter={'_id': submissions[0][str(0)]},
    )
    assert e is not None  # now also in valid submissions


@pytest.mark.asyncio
async def test_verifying_valid_verification_token_submission_replacement(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that previously verified submission is replaced with a new one."""
    path = f'/users/{username}/surveys/{survey_name}'
    await client.post(url=path, headers=headers, json=configuration)
    # push first submission
    submission = submissions[0]
    email_address = submission[str(0)]
    await client.post(url=f'{path}/submissions', json=submission)
    await client.get(
        url=f'{path}/verification/{str(0).zfill(64)}',
        allow_redirects=False,
    )
    # push second submission with the same email address
    submission = copy.deepcopy(submissions[1])
    submission[str(0)] = email_address
    await client.post(url=f'{path}/submissions', json=submission)
    await client.get(
        url=f'{path}/verification/{str(1).zfill(64)}',
        allow_redirects=False,
    )
    survey = await main.survey_manager.fetch(username, survey_name)
    x = await survey.submissions.find_one({'_id': email_address})
    assert x['data'] == submission


@pytest.mark.asyncio
async def test_verifying_invalid_verification_token(
        mock_email_sending,
        mock_verification_token_generation,
        client,
        headers,
        username,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that request is rejected given an invalid verification token."""
    path = f'/users/{username}/surveys/{survey_name}'
    await client.post(url=path, headers=headers, json=configuration)
    response = await client.get(
        url=f'{path}/verification/{str(1).zfill(64)}',
        allow_redirects=False,
    )
    assert response.status_code == 401
    survey = await main.survey_manager.fetch(username, survey_name)
    x = await survey.submissions.find_one({})
    assert x is None


@pytest.mark.asyncio
async def test_duplicate_verification_token_resolution(
        mock_email_sending,
        mock_verification_token_generation_with_duplication,
        client,
        headers,
        username,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test submission is correctly verified given valid verification token."""
    path = f'/users/{username}/surveys/{survey_name}'
    await client.post(url=path, headers=headers, json=configuration)
    for submission in submissions[:2]:
        await client.post(url=f'{path}/submissions', json=submission)
    survey = await main.survey_manager.fetch(username, survey_name)
    for i in range(2):
        e = await survey.unverified_submissions.find_one(
            filter={'_id': str(i).zfill(64)},
        )
        assert e is not None


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
        configurations,
        submissionss,
        resultss,
        cleanup,
    ):
    """Test that aggregating test submissions returns the correct result."""
    counter = 0
    for survey_name, configuration in configurations.items():
        path = f'/users/{username}/surveys/{survey_name}'
        await client.post(
            url=path,
            headers=headers,
            json=configuration,
        )
        survey = await main.survey_manager.fetch(username, survey_name)
        # push test submissions and validate them
        for submission in submissionss[survey_name]:
            await client.post(url=f'{path}/submissions', json=submission)
            if survey.index is not None:
                await client.get(
                    url=f'{path}/verification/{str(counter).zfill(64)}',
                    allow_redirects=False,
                )
                counter += 1
        # aggregate and fetch results
        response = await client.get(url=f'{path}/results', headers=headers)
        assert response.status_code == 200
        assert response.json() == resultss[survey_name]


@pytest.mark.asyncio
async def test_fetching_results_without_submissions(
        client,
        headers,
        username,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that aggregation works when no submissions have yet been made."""
    path = f'/users/{username}/surveys/{survey_name}'
    await client.post(url=path, headers=headers, json=configuration)
    response = await client.get(url=f'{path}/results', headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        'count': 0,
        'data': [
            None,
            0,
            [0, 0, 0, 0],
            [0, 0, 0],
            None,
        ]
    }


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
    response = await client.post(
        f'/authentication',
        json={'identifier': username, 'password': password},
    )
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
        json={'verification_token': str(0).zfill(64), 'password': password},
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
        json={'verification_token': str(0).zfill(64), 'password': password},
    )
    response = await client.post(
        url='/authentication',
        json={'identifier': 'kangaroo', 'password': password},
    )
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
        json={'verification_token': str(0).zfill(64), 'password': password},
    )
    response = await client.post(
        url='/authentication',
        json={'identifier': username, 'password': 'kangaroo'},
    )
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
        json={'verification_token': str(0).zfill(64), 'password': password},
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
        json={'verification_token': str(1).zfill(64), 'password': password},
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
        json={'verification_token': str(0).zfill(64), 'password': 'kangaroo'},
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
    verification_credentials = {
        'verification_token': str(0).zfill(64),
        'password': password,
    }
    await client.post(url='/verification', json=verification_credentials)
    response = await client.post(
        url='/verification',
        json=verification_credentials,
    )
    assert check_error(response, errors.InvalidVerificationTokenError)
    response = await client.get(f'/users/{username}', headers=headers)
    assert response.json()['verified']
