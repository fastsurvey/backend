import pytest
import httpx
import copy

import app.main as main
import app.survey as sve
import app.resources.database as database
import app.authentication as auth
import app.errors as errors

import tests.conftest as conftest


@pytest.fixture(scope='module')
async def client():
    """Provide a HTTPX AsyncClient that is properly closed after testing."""
    client = httpx.AsyncClient(app=main.app, base_url='http://example.com')
    yield client
    await client.aclose()


@pytest.fixture(scope='function')
@pytest.mark.asyncio
async def headers(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
    ):
    """Create a user and provide a valid authentication header."""
    await client.post(f'/users/{username}', json=account_data)
    await client.post(
        url='/verification',
        json={'verification_token': conftest.valid_token()},
    )
    res = await client.post(
        url='/authentication',
        json={
            'identifier': account_data['username'],
            'password': account_data['password'],
        },
    )
    access_token = res.json()['access_token']
    return {'Authorization': f'Bearer {access_token}'}


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
        client,
        headers,
        username,
        cleanup,
    ):
    """Test that correct account data is returned on valid request."""
    res = await client.get(f'/users/{username}', headers=headers)
    assert res.status_code == 200
    assert set(res.json().keys()) == {'email_address', 'verified'}


@pytest.mark.asyncio
async def test_fetching_existing_user_with_invalid_access_token(
        client,
        headers,
        username,
        cleanup,
    ):
    """Test that request is correctly rejected for invalid access token."""
    headers = {'Authorization': f'Bearer {conftest.invalid_token()}'}
    res = await client.get(f'/users/{username}', headers=headers)
    assert check_error(res, errors.InvalidAccessTokenError)


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
    res = await client.post(url=f'/users/{username}', json=account_data)
    assert res.status_code == 200
    entry = await database.database['accounts'].find_one({})
    assert entry['username'] == username


@pytest.mark.asyncio
async def test_creating_user_with_invalid_account_data(
        client,
        invalid_account_datas,
    ):
    """Test that account creation fails when given invalid account data."""
    account_data = invalid_account_datas[0]
    username = account_data['username']
    res = await client.post(url=f'/users/{username}', json=account_data)
    assert check_error(res, None)
    entry = await database.database['accounts'].find_one({})
    assert entry is None


@pytest.mark.asyncio
async def test_creating_user_with_username_mismatch_in_route_and_body(
        client,
        account_data,
    ):
    """Test that account creation fails when given invalid account data."""
    res = await client.post(url=f'/users/kangaroo', json=account_data)
    assert check_error(res, None)
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
    duplicate = copy.deepcopy(account_datas[1])
    duplicate['username'] = username
    res = await client.post(url=f'/users/{username}', json=duplicate)
    assert check_error(res, errors.UsernameAlreadyTakenError)
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
    duplicate = copy.deepcopy(account_datas[1])
    duplicate['email_address'] = email_address
    res = await client.post(
        url=f'/users/{duplicate["username"]}',
        json=duplicate,
    )
    assert check_error(res, errors.EmailAddressAlreadyTakenError)
    entry = await database.database['accounts'].find_one({})
    assert entry['username'] == username


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
        client,
        headers,
        username,
        account_data,
        cleanup,
):
    """Test that account is correctly updated given valid account data."""
    x = await database.database['accounts'].find_one({})
    res = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert res.status_code == 200
    assert x == await database.database['accounts'].find_one({})


@pytest.mark.asyncio
async def test_updating_existing_user_with_valid_password(
        client,
        headers,
        username,
        account_data,
        account_datas,
        cleanup,
):
    """Test that account is correctly updated given valid account data."""
    account_data = copy.deepcopy(account_data)
    account_data['password'] = account_datas[1]['password']
    res = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert res.status_code == 200
    x = await database.database['accounts'].find_one({})
    assert auth.verify_password(
        password=account_data['password'],
        password_hash=x['password_hash'],
    )


@pytest.mark.skip(reason='todo')
@pytest.mark.asyncio
async def test_updating_existing_user_with_valid_email_address_in_use(
        client,
        headers,
        username,
        account_data,
        account_datas,
        cleanup,
):
    """Test that updating the email address to one in use fails correctly."""
    await client.post(
        url=f'/users/{account_datas[1]["username"]}',
        json=account_datas[1],
    )
    account_data = copy.deepcopy(account_data)
    account_data['email_address'] = account_datas[1]['email_address']
    res = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert check_error(res, errors.EmailAddressAlreadyTakenError)


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
    sve.CACHE.reset()
    res = await client.get(f'/users/{username}/surveys/{survey_name}')
    assert res.status_code == 200
    assert res.json() == configuration


@pytest.mark.asyncio
async def test_fetching_nonexistent_survey(client, username):
    """Test that exception is raised when requesting a nonexistent survey."""
    res = await client.get(f'/users/{username}/surveys/complex')
    assert check_error(res, errors.SurveyNotFoundError)


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
    sve.CACHE.reset()
    res = await client.get(f'/users/{username}/surveys/{survey_name}')
    assert check_error(res, errors.SurveyNotFoundError)


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
    res = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert res.status_code == 200
    assert sve.CACHE.fetch(username, survey_name)
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
        cleanup,
    ):
    """Test that survey creation fails with an invalid configuration."""
    configuration = invalid_configurationss[survey_name][0]
    res = await client.post(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert check_error(res, None)
    with pytest.raises(KeyError):
        sve.CACHE.fetch(username, survey_name)
    entry = await database.database['configurations'].find_one()
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
    res = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert res.status_code == 200
    survey = sve.CACHE.fetch(username, survey_name)
    assert survey.configuration['description'] == configuration['description']
    entry = await database.database['configurations'].find_one()
    assert entry['description'] == configuration['description']


@pytest.mark.asyncio
async def test_updating_nonexistent_survey_with_valid_configuration(
        client,
        headers,
        username,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey update fails when the survey does not exist."""
    res = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert check_error(res, errors.SurveyNotFoundError)
    with pytest.raises(KeyError):
        sve.CACHE.fetch(username, survey_name)
    entry = await database.database['configurations'].find_one()
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
    res = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert res.status_code == 200
    assert sve.CACHE.fetch(username, 'kangaroo')
    entry = await database.database['configurations'].find_one()
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
    res = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert check_error(res, errors.SurveyNameAlreadyTakenError)
    assert sve.CACHE.fetch(username, survey_name)
    entry = await database.database['configurations'].find_one(
        filter={'survey_name': survey_name},
    )
    assert entry is not None


@pytest.mark.asyncio
async def test_updating_survey_with_existing_submissions(
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
        url=f'{path}/verification/{conftest.valid_token()}',
        allow_redirects=False,
    )
    # push changed configuration
    configuration = copy.deepcopy(configuration)
    configuration['description'] = 'chameleon'
    res = await client.put(url=path, headers=headers, json=configuration)
    # check validity
    assert check_error(res, errors.SubmissionsExistError)
    survey = sve.CACHE.fetch(username, survey_name)
    assert survey.configuration['description'] != configuration['description']
    entry = await database.database['configurations'].find_one()
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
    survey = await sve.fetch(username, survey_name)
    res = await client.post(url=f'{path}/submissions', json=submissions[0])
    assert res.status_code == 200
    entry = await survey.unverified_submissions.find_one()
    assert entry['submission'] == submissions[0]


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
    survey = await sve.fetch(username, survey_name)
    res = await client.post(
        url=f'{path}/submissions',
        json=invalid_submissionss[survey_name][0],
    )
    assert check_error(res, None)
    entry = await survey.unverified_submissions.find_one()
    assert entry is None


################################################################################
# Verify submission
################################################################################


@pytest.mark.asyncio
async def test_verifying_valid_verification_token(
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
    verification_token = conftest.valid_token()
    res = await client.get(
        url=f'{path}/verification/{verification_token}',
        allow_redirects=False,
    )
    assert res.status_code == 307
    survey = await sve.fetch(username, survey_name)
    e = await survey.unverified_submissions.find_one(
        filter={'_id': auth.hash_token(verification_token)},
    )
    assert e is not None  # still unchanged in unverified submissions
    e = await survey.submissions.find_one(
        filter={'_id': submissions[0][str(0)]},
    )
    assert e is not None  # now also in valid submissions


@pytest.mark.asyncio
async def test_verifying_valid_verification_token_submission_replacement(
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
        url=f'{path}/verification/{conftest.valid_token()}',
        allow_redirects=False,
    )
    # push second submission with the same email address
    submission = copy.deepcopy(submissions[1])
    submission[str(0)] = email_address
    await client.post(url=f'{path}/submissions', json=submission)
    await client.get(
        url=f'{path}/verification/{conftest.valid_token()}',
        allow_redirects=False,
    )
    survey = await sve.fetch(username, survey_name)
    x = await survey.submissions.find_one({'_id': email_address})
    assert x['submission'] == submission


@pytest.mark.asyncio
async def test_verifying_invalid_verification_token(
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
    res = await client.get(
        url=f'{path}/verification/{conftest.invalid_token()}',
        allow_redirects=False,
    )
    assert res.status_code == 401
    survey = await sve.fetch(username, survey_name)
    x = await survey.submissions.find_one({})
    assert x is None


################################################################################
# Fetch Results
################################################################################


@pytest.mark.asyncio
async def test_fetching_results(
        client,
        headers,
        username,
        configurations,
        submissionss,
        resultss,
        cleanup,
    ):
    """Test that aggregating test submissions returns the correct result."""
    for survey_name, configuration in configurations.items():
        path = f'/users/{username}/surveys/{survey_name}'
        await client.post(url=path, headers=headers, json=configuration)
        # push test submissions and validate them
        for submission in submissionss[survey_name]:
            await client.post(url=f'{path}/submissions', json=submission)
            await client.get(
                url=f'{path}/verification/{conftest.valid_token()}',
                allow_redirects=False,
            )
        # aggregate and fetch results
        res = await client.get(url=f'{path}/results', headers=headers)
        assert res.status_code == 200
        assert res.json() == resultss[survey_name]


@pytest.mark.asyncio
async def test_fetching_results_without_submissions(
        client,
        headers,
        username,
        survey_name,
        configuration,
        default_resultss,
        cleanup,
    ):
    """Test that aggregation works when no submissions have yet been made."""
    path = f'/users/{username}/surveys/{survey_name}'
    await client.post(url=path, headers=headers, json=configuration)
    res = await client.get(url=f'{path}/results', headers=headers)
    assert res.status_code == 200
    assert res.json() == default_resultss[survey_name]


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
    res = await client.post(
        f'/authentication',
        json={'identifier': username, 'password': password},
    )
    assert check_error(res, errors.AccountNotVerifiedError)


@pytest.mark.asyncio
async def test_generating_access_token_with_valid_credentials(
        mock_email_sending,
        mock_token_generation,
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
        json={'verification_token': conftest.valid_token()},
    )
    # test with username as well as email address as identifier
    for identifier in [username, email_address]:
        res = await client.post(
            url='/authentication',
            json={'identifier': identifier, 'password': password},
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_generating_access_token_invalid_username(
        client,
        username,
        password,
    ):
    """Test that authentication fails for a user that does not exist."""
    res = await client.post(
        url='/authentication',
        json={'identifier': username, 'password': password},
    )
    assert check_error(res, errors.UserNotFoundError)


@pytest.mark.asyncio
async def test_generating_access_token_with_invalid_password(
        mock_email_sending,
        mock_token_generation,
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
        json={'verification_token': conftest.valid_token()},
    )
    res = await client.post(
        url='/authentication',
        json={'identifier': username, 'password': 'kangaroo'},
    )
    assert check_error(res, errors.InvalidPasswordError)


################################################################################
# Verify Email Address
################################################################################


@pytest.mark.asyncio
async def test_verifying_email_address_with_invalid_verification_token(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that email verification fails with invalid verification token."""
    await client.post(url=f'/users/{username}', json=account_data)
    res = await client.post(
        url=f'/verification',
        json={'verification_token': conftest.invalid_token()},
    )
    assert check_error(res, errors.InvalidVerificationTokenError)
    x = await database.database['accounts'].find_one({'username': username})
    assert not x['verified']


@pytest.mark.asyncio
async def test_verifying_previously_verified_email_address(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that email verification works given valid credentials."""
    await client.post(url=f'/users/{username}', json=account_data)
    await client.post(
        url='/verification',
        json={'verification_token': conftest.valid_token()},
    )
    res = await client.post(
        url='/verification',
        json={'verification_token': conftest.valid_token()},
    )
    assert check_error(res, errors.InvalidVerificationTokenError)
    x = await database.database['accounts'].find_one({'username': username})
    assert x['verified']
