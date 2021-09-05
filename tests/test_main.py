import pytest
import httpx
import copy

import app.main as main
import app.survey as sve
import app.resources.database as database
import app.authentication as auth
import app.errors as errors

import tests.conftest as conftest


################################################################################
# Helper Functions
################################################################################


@pytest.fixture(scope='module')
async def client():
    """Provide a HTTPX AsyncClient that is properly closed after testing."""
    client = httpx.AsyncClient(app=main.app, base_url='http://example.com')
    yield client
    await client.aclose()


async def setup_account(client, username, account_data):
    """Create a test account."""
    return await client.post(f'/users/{username}', json=account_data)


async def setup_account_verification(client):
    """Verify most recently created test account."""
    return await client.post(
        url='/verification',
        json={'verification_token': conftest.valid_token()},
    )


async def setup_headers(client, account_data):
    """Provide a valid authentication header for the test account."""
    res = await client.post(
        url='/authentication',
        json={
            'identifier': account_data['username'],
            'password': account_data['password'],
        },
    )
    access_token = res.json()['access_token']
    return {'Authorization': f'Bearer {access_token}'}


async def setup_survey(client, headers, username, configuration):
    """Create a survey on the given account."""
    return await client.post(
        url=f'/users/{username}/surveys/{configuration["survey_name"]}',
        headers=headers,
        json=configuration,
    )


async def setup_submission(client, username, survey_name, submission):
    """Create a submission for the given survey."""
    return await client.post(
        url=f'/users/{username}/surveys/{survey_name}/submissions',
        json=submission,
    )


async def setup_submission_verification(client, username, survey_name):
    """Verify most recently created test submission."""
    base = f'/users/{username}/surveys/{survey_name}'
    return await client.get(
        url=f'{base}/verification/{conftest.valid_token()}',
        allow_redirects=False,
    )


def check_error(response, error):
    """Check that a HTTPX request returned with a specific error.

    TODO use an error value of None to mean no error (status code 200)

    """
    if error is None:
        return response.status_code == 422
    return (
        response.status_code == error.STATUS_CODE
        and response.json()['detail'] == error.DETAIL
    )


################################################################################
# Route: Status
################################################################################


@pytest.mark.asyncio
async def test_fetching_server_status(client):
    """Test that correct status data is returned."""
    res = await client.get(f'/status')
    assert res.status_code == 200
    assert set(res.json().keys()) == {'commit_sha', 'branch_name', 'start_time'}


################################################################################
# Route: Fetch User
################################################################################


@pytest.mark.asyncio
async def test_fetching_verified_account_with_valid_access_token(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that correct account data is returned on valid request."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    res = await client.get(f'/users/{username}', headers=headers)
    assert res.status_code == 200
    assert set(res.json().keys()) == {'email_address', 'verified'}


@pytest.mark.asyncio
async def test_fetching_verified_account_with_invalid_access_token(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that request is correctly rejected for invalid access token."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = {'Authorization': f'Bearer {conftest.invalid_token()}'}
    res = await client.get(f'/users/{username}', headers=headers)
    assert check_error(res, errors.InvalidAccessTokenError)


################################################################################
# Route: Create User
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
    res = await setup_account(client, username, account_data)
    assert res.status_code == 200
    e = await database.database['accounts'].find_one()
    assert e['username'] == username


@pytest.mark.asyncio
async def test_creating_user_with_invalid_account_data(
        client,
        invalid_account_datas,
    ):
    """Test that account creation fails when given invalid account data."""
    account_data = invalid_account_datas[0]
    res = await setup_account(client, account_data['username'], account_data)
    assert check_error(res, None)
    e = await database.database['accounts'].find_one()
    assert e is None


@pytest.mark.asyncio
async def test_creating_user_with_username_mismatch_in_route_and_body(
        client,
        account_data,
    ):
    """Test that account creation fails when given invalid account data."""
    res = await setup_account(client, 'kangaroo', account_data)
    assert check_error(res, None)
    e = await database.database['accounts'].find_one({})
    assert e is None


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
    await setup_account(client, username, account_data)
    duplicate = copy.deepcopy(account_datas[1])
    duplicate['username'] = username
    res = await setup_account(client, username, duplicate)
    assert check_error(res, errors.UsernameAlreadyTakenError)
    e = await database.database['accounts'].find_one({})
    assert e['email_address'] == email_address


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
    await setup_account(client, username, account_data)
    duplicate = copy.deepcopy(account_datas[1])
    duplicate['email_address'] = email_address
    res = await setup_account(client, duplicate['username'], duplicate)
    assert check_error(res, errors.EmailAddressAlreadyTakenError)
    e = await database.database['accounts'].find_one({})
    assert e['username'] == username


################################################################################
# Route: Update User
################################################################################


# TODO test_updating_existing_user_with_valid_email_address_not_in_use
# TODO test_updating_existing_user_with_valid_email_address_in_use
# TODO update all fields at the same time


@pytest.mark.asyncio
async def test_updating_existing_user_with_no_changes(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that account is correctly updated given valid account data."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    e = await database.database['accounts'].find_one()
    res = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert res.status_code == 200
    assert e == await database.database['accounts'].find_one()


@pytest.mark.asyncio
async def test_updating_existing_user_with_valid_username_not_in_use(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        account_datas,
        configuration,
        cleanup,
    ):
    """Test that account is correctly updated given valid account data."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    account_data = copy.deepcopy(account_data)
    account_data['username'] = account_datas[1]['username']
    res = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert res.status_code == 200
    e = await database.database['accounts'].find_one()
    assert account_data['username'] == e['username']
    e = await database.database['configurations'].find_one()
    assert account_data['username'] == e['username']
    e = await database.database['access_tokens'].find_one()
    assert account_data['username'] == e['username']


@pytest.mark.asyncio
async def test_updating_existing_user_with_valid_username_in_use(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        email_address,
        account_data,
        account_datas,
        cleanup,
    ):
    """Test that account update is rejected if the new username is in use."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_account(client, account_datas[1]['username'], account_datas[1])
    account_data = copy.deepcopy(account_data)
    account_data['username'] = account_datas[1]['username']
    res = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert check_error(res, errors.UsernameAlreadyTakenError)
    e = await database.database['accounts'].find_one(
        filter={'email_address': email_address},
    )
    assert username == e['username']



@pytest.mark.asyncio
async def test_updating_existing_user_with_valid_password(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        account_datas,
        cleanup,
    ):
    """Test that account is correctly updated given valid account data."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    account_data = copy.deepcopy(account_data)
    account_data['password'] = account_datas[1]['password']
    res = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert res.status_code == 200
    e = await database.database['accounts'].find_one()
    assert auth.verify_password(account_data['password'], e['password_hash'])


@pytest.mark.skip(reason='todo')
@pytest.mark.asyncio
async def test_updating_existing_user_with_valid_email_address_in_use(
        mock_email_sending,
        mock_token_generation,
        client,
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


################################################################################
# Route: Delete User
################################################################################


@pytest.mark.asyncio
async def test_deleting_existing_user(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that all data is correctly wiped when a user is deleted."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, survey_name, submissions[0])
    await setup_submission_verification(client, username, survey_name)
    survey = await sve.fetch(username, survey_name)
    res = await client.delete(url=f'/users/{username}', headers=headers)
    assert res.status_code == 200
    assert await database.database['accounts'].find_one() is None
    assert await database.database['access_tokens'].find_one() is None
    assert await database.database['configurations'].find_one() is None
    assert await survey.submissions.find_one() is None
    assert await survey.unverified_submissions.find_one() is None


################################################################################
# Route: Fetch Surveys
################################################################################


@pytest.mark.asyncio
async def test_fetching_existing_surveys(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        configurations,
        cleanup,
    ):
    """Test that correct configurations of a specific user are returned."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    for configuration in configurations.values():
        await setup_survey(client, headers, username, configuration)
    res = await client.get(url=f'/users/{username}/surveys', headers=headers)
    assert res.status_code == 200
    assert res.json() == sorted(
        configurations.values(),
        key=lambda x: x['start'],
        reverse=True,
    )


@pytest.mark.asyncio
async def test_fetching_nonexistent_surveys(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that an empty list is returned when no surveys exist."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    res = await client.get(url=f'/users/{username}/surveys', headers=headers)
    assert res.status_code == 200
    assert res.json() == []


################################################################################
# Route: Fetch Survey
################################################################################


@pytest.mark.asyncio
async def test_fetching_existing_survey(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that correct configuration is returned for an existing survey."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    res = await client.get(f'/users/{username}/surveys/{survey_name}')
    assert res.status_code == 200
    assert res.json() == configuration


@pytest.mark.asyncio
async def test_fetching_nonexistent_survey(client, username, survey_name):
    """Test that exception is raised when requesting a nonexistent survey."""
    res = await client.get(f'/users/{username}/surveys/{survey_name}')
    assert check_error(res, errors.SurveyNotFoundError)


@pytest.mark.asyncio
async def test_fetching_survey_in_draft_mode(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that exception is raised when requesting a survey in draft mode."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    configuration = copy.deepcopy(configuration)
    configuration['draft'] = True
    await setup_survey(client, headers, username, configuration)
    res = await client.get(f'/users/{username}/surveys/{survey_name}')
    assert check_error(res, errors.SurveyNotFoundError)


################################################################################
# Route: Create Survey
################################################################################


@pytest.mark.asyncio
async def test_creating_survey_with_valid_configuration(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey is correctly created given a valid configuration."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    res = await setup_survey(client, headers, username, configuration)
    assert res.status_code == 200
    e = await database.database['configurations'].find_one()
    assert e['username'] == username
    assert e['survey_name'] == survey_name


@pytest.mark.asyncio
async def test_creating_survey_with_invalid_configuration(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        invalid_configurationss,
        cleanup,
    ):
    """Test that survey creation fails with an invalid configuration."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    configuration = invalid_configurationss[survey_name][0]
    res = await setup_survey(client, headers, username, configuration)
    assert check_error(res, None)
    e = await database.database['configurations'].find_one()
    assert e is None


################################################################################
# Route: Update Survey
################################################################################


@pytest.mark.asyncio
async def test_updating_existing_survey_with_valid_configuration(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey is correctly updated given a valid configuration."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    configuration = copy.deepcopy(configuration)
    configuration['description'] = 'Hello World!'
    res = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert res.status_code == 200
    e = await database.database['configurations'].find_one()
    assert e['description'] == configuration['description']


@pytest.mark.asyncio
async def test_updating_nonexistent_survey_with_valid_configuration(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey update fails when the survey does not exist."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    res = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert check_error(res, errors.SurveyNotFoundError)
    e = await database.database['configurations'].find_one()
    assert e is None


@pytest.mark.asyncio
async def test_updating_survey_name_to_survey_name_not_in_use(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey name is updated when it is not already used."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    configuration = copy.deepcopy(configuration)
    configuration['survey_name'] = 'kangaroo'
    res = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert res.status_code == 200
    e = await database.database['configurations'].find_one()
    assert e['survey_name'] == 'kangaroo'


@pytest.mark.asyncio
async def test_updating_survey_name_to_survey_name_in_use(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        cleanup,
    ):
    """Test that survey name update fails if survey name is already in use."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    configuration = copy.deepcopy(configuration)
    configuration['survey_name'] = 'kangaroo'
    await setup_survey(client, headers, username, configuration)
    res = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert check_error(res, errors.SurveyNameAlreadyTakenError)
    e = await database.database['configurations'].find_one(
        filter={'survey_name': survey_name},
    )
    assert e is not None


@pytest.mark.asyncio
async def test_updating_survey_with_existing_submissions(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that survey name update fails if it has existing submissions."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, survey_name, submissions[0])
    configuration = copy.deepcopy(configuration)
    configuration['survey_name'] = 'kangaroo'
    res = await client.put(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
        json=configuration,
    )
    assert check_error(res, errors.SubmissionsExistError)
    e = await database.database['configurations'].find_one()
    assert e['survey_name'] == survey_name


################################################################################
# Route: Reset Survey
################################################################################


@pytest.mark.asyncio
async def test_resetting_survey_with_existing_submissions(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that verified and unverified submissions are correctly deleted."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, survey_name, submissions[0])
    await setup_submission_verification(client, username, survey_name)
    survey = await sve.fetch(username, survey_name)
    res = await client.delete(
        url=f'/users/{username}/surveys/{survey_name}/submissions',
        headers=headers,
    )
    assert res.status_code == 200
    assert await database.database['configurations'].find_one() is not None
    assert await survey.submissions.find_one() is None
    assert await survey.unverified_submissions.find_one() is None


################################################################################
# Route: Delete Survey
################################################################################


@pytest.mark.asyncio
async def test_deleting_existing_survey_with_existing_submissions(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that a survey including all submissions is correctly deleted."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, survey_name, submissions[0])
    await setup_submission_verification(client, username, survey_name)
    survey = await sve.fetch(username, survey_name)
    res = await client.delete(
        url=f'/users/{username}/surveys/{survey_name}',
        headers=headers,
    )
    assert res.status_code == 200
    assert await database.database['configurations'].find_one() is None
    assert await survey.submissions.find_one() is None
    assert await survey.unverified_submissions.find_one() is None


################################################################################
# Route: Create Submission
#
# It suffices here to test only one valid and one invalid submission, instead
# of all examples that we have, as the validation is tested on its own.
################################################################################


@pytest.mark.asyncio
async def test_creating_submission(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that submission works given a valid submission."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    res = await setup_submission(client, username, survey_name, submissions[0])
    assert res.status_code == 200
    survey = await sve.fetch(username, survey_name)
    e = await survey.unverified_submissions.find_one()
    assert e['submission'] == submissions[0]


@pytest.mark.asyncio
async def test_creating_invalid_submission(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        invalid_submissionss,
        cleanup,
    ):
    """Test that submit correctly fails given an invalid submissions."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    submission = invalid_submissionss[survey_name][0]
    res = await setup_submission(client, username, survey_name, submission)
    assert check_error(res, None)
    survey = await sve.fetch(username, survey_name)
    e = await survey.unverified_submissions.find_one()
    assert e is None


################################################################################
# Route: Verify Submission
################################################################################


@pytest.mark.asyncio
async def test_verifying_valid_verification_token(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test submission is correctly verified given valid verification token."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, survey_name, submissions[0])
    res = await setup_submission_verification(client, username, survey_name)
    assert res.status_code == 307
    survey = await sve.fetch(username, survey_name)
    e = await survey.unverified_submissions.find_one(
        filter={'_id': auth.hash_token(conftest.valid_token())},
    )
    assert e is not None  # still unchanged in unverified submissions
    e = await survey.submissions.find_one({'_id': submissions[0][str(0)]})
    assert e is not None  # now also in valid submissions


@pytest.mark.asyncio
async def test_verifying_valid_verification_token_submission_replacement(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that previously verified submission is replaced with a new one."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    # submit and verify first submission
    await setup_submission(client, username, survey_name, submissions[0])
    await setup_submission_verification(client, username, survey_name)
    # submit and verify second submission with the same email address
    email_address = submissions[0][str(0)]
    submission = copy.deepcopy(submissions[1])
    submission[str(0)] = email_address
    await setup_submission(client, username, survey_name, submission)
    await setup_submission_verification(client, username, survey_name)
    survey = await sve.fetch(username, survey_name)
    e = await survey.submissions.find_one({'_id': email_address})
    assert e['submission'] == submission


@pytest.mark.asyncio
async def test_verifying_invalid_verification_token(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        submissions,
        cleanup,
    ):
    """Test that request is rejected given an invalid verification token."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, survey_name, submissions[0])
    path = f'/users/{username}/surveys/{survey_name}'
    res = await client.get(
        url=f'{path}/verification/{conftest.invalid_token()}',
        allow_redirects=False,
    )
    assert res.status_code == 401
    survey = await sve.fetch(username, survey_name)
    e = await survey.submissions.find_one()
    assert e is None


################################################################################
# Route: Fetch Results
################################################################################


@pytest.mark.asyncio
async def test_fetching_results(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        configurations,
        submissionss,
        resultss,
        cleanup,
    ):
    """Test that aggregating test submissions returns the correct result."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    for survey_name, configuration in configurations.items():
        await setup_survey(client, headers, username, configuration)
        for submission in submissionss[survey_name]:
            await setup_submission(client, username, survey_name, submission)
            await setup_submission_verification(client, username, survey_name)
        res = await client.get(
            url=f'/users/{username}/surveys/{survey_name}/results',
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json() == resultss[survey_name]


@pytest.mark.asyncio
async def test_fetching_results_without_submissions(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        survey_name,
        configuration,
        default_resultss,
        cleanup,
    ):
    """Test that aggregation works when no submissions have yet been made."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    res = await client.get(
        url=f'/users/{username}/surveys/{survey_name}/results',
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json() == default_resultss[survey_name]


################################################################################
# Route: Login
################################################################################


@pytest.mark.asyncio
async def test_logging_in_with_non_verified_account(
        mock_email_sending,
        client,
        username,
        password,
        account_data,
        cleanup,
    ):
    """Test that authentication fails when the account is not verified."""
    await setup_account(client, username, account_data)
    res = await client.post(
        url='/authentication',
        json={'identifier': username, 'password': password},
    )
    assert check_error(res, errors.AccountNotVerifiedError)


@pytest.mark.asyncio
async def test_logging_in_with_valid_credentials(
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
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    # test with username as well as email address as identifier
    for identifier in [username, email_address]:
        res = await client.post(
            url='/authentication',
            json={'identifier': identifier, 'password': password},
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_logging_in_invalid_username(
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
async def test_logging_in_with_invalid_password(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that authentication fails given an incorrect password."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    res = await client.post(
        url='/authentication',
        json={'identifier': username, 'password': 'kangaroo'},
    )
    assert check_error(res, errors.InvalidPasswordError)


################################################################################
# Route: Logout
################################################################################


@pytest.mark.asyncio
async def test_logging_out_existing_access_token(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that logout flow works correctly."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    res = await client.delete(url='/authentication', headers=headers)
    assert res.status_code == 200
    assert await database.database['access_token'].find_one() is None
    # try changing account data with old access token
    res = await client.put(
        url=f'/users/{username}',
        headers=headers,
        json=account_data,
    )
    assert check_error(res, errors.InvalidAccessTokenError)


################################################################################
# Route: Verify Email Address
################################################################################


@pytest.mark.asyncio
async def test_verifying_email_address_with_valid_verification_token(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that email verification succeeds given valid verification token."""
    await setup_account(client, username, account_data)
    res = await setup_account_verification(client)
    assert res.status_code == 200
    e = await database.database['accounts'].find_one({'username': username})
    assert e['verified']


@pytest.mark.asyncio
async def test_verifying_email_address_with_invalid_verification_token(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that email verification fails given invalid verification token."""
    await setup_account(client, username, account_data)
    res = await client.post(
        url=f'/verification',
        json={'verification_token': conftest.invalid_token()},
    )
    assert check_error(res, errors.InvalidVerificationTokenError)
    e = await database.database['accounts'].find_one({'username': username})
    assert not e['verified']


@pytest.mark.asyncio
async def test_verifying_previously_verified_email_address(
        mock_email_sending,
        mock_token_generation,
        client,
        username,
        account_data,
        cleanup,
    ):
    """Test that verification succeeds even if account is already verified."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    res = await setup_account_verification(client)
    assert res.status_code == 200
    e = await database.database['accounts'].find_one({'username': username})
    assert e['verified']
