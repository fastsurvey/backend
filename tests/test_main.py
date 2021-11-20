import pytest
import httpx
import copy

import app.main as main
import app.survey as survey
import app.database as database
import app.auth as auth
import app.errors as errors

import tests.conftest as conftest


########################################################################################
# Helper Functions
########################################################################################


@pytest.fixture(scope="module")
async def client():
    """Provide a HTTPX AsyncClient that is properly closed after testing."""
    client = httpx.AsyncClient(app=main.app, base_url="http://example.com")
    yield client
    await client.aclose()


async def setup_account(client, username, account_data):
    """Create a test account."""
    return await client.post(f"/users", json=account_data)


async def setup_account_verification(client):
    """Verify most recently created test account."""
    return await client.post(
        url="/verification",
        json={"verification_token": conftest.valid_token()},
    )


async def setup_headers(client, account_data):
    """Provide a valid authentication header for the test account."""
    res = await client.post(
        url="/authentication",
        json={
            "identifier": account_data["username"],
            "password": account_data["password"],
        },
    )
    access_token = res.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


async def setup_survey(client, headers, username, configuration):
    """Create a survey on the given account."""
    return await client.post(
        url=f"/users/{username}/surveys",
        headers=headers,
        json=configuration,
    )


async def setup_submission(client, username, survey_name, submission):
    """Create a submission for the given survey."""
    return await client.post(
        url=f"/users/{username}/surveys/{survey_name}/submissions",
        json=submission,
    )


def fails(response, error):
    """Check that a HTTPX request returned with a specific error."""
    if error is None:
        return response.status_code == 200
    return (
        response.status_code == error.STATUS_CODE
        and response.json()["detail"] == error.DETAIL
    )


########################################################################################
# Route: Status
########################################################################################


@pytest.mark.asyncio
async def test_reading_server_status(client):
    """Test that correct status data is returned."""
    res = await client.get(f"/status")
    assert fails(res, None)
    assert set(res.json().keys()) == {
        "environment",
        "commit_sha",
        "branch_name",
        "start_time",
    }


########################################################################################
# Route: Read User
########################################################################################


@pytest.mark.asyncio
async def test_reading_verified_account_with_valid_access_token(
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
    res = await client.get(f"/users/{username}", headers=headers)
    assert fails(res, None)
    assert set(res.json().keys()) == {"email_address", "verified"}


@pytest.mark.asyncio
async def test_reading_verified_account_with_invalid_access_token(
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
    headers = {"Authorization": f"Bearer {conftest.invalid_token()}"}
    res = await client.get(f"/users/{username}", headers=headers)
    assert fails(res, errors.InvalidAccessTokenError)


########################################################################################
# Route: Create User
########################################################################################


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
    assert fails(res, None)
    e = await database.database["accounts"].find_one()
    assert e["username"] == username


@pytest.mark.asyncio
async def test_creating_user_with_invalid_account_data(
    client,
    invalid_account_datas,
):
    """Test that account creation fails when given invalid account data."""
    account_data = invalid_account_datas[0]
    res = await setup_account(client, account_data["username"], account_data)
    assert fails(res, errors.InvalidSyntaxError)
    e = await database.database["accounts"].find_one()
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
    duplicate["username"] = username
    res = await setup_account(client, username, duplicate)
    assert fails(res, errors.UsernameAlreadyTakenError)
    e = await database.database["accounts"].find_one({})
    assert e["email_address"] == email_address


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
    duplicate["email_address"] = email_address
    res = await setup_account(client, duplicate["username"], duplicate)
    assert fails(res, errors.EmailAddressAlreadyTakenError)
    e = await database.database["accounts"].find_one({})
    assert e["username"] == username


########################################################################################
# Route: Update User
########################################################################################


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
    e = await database.database["accounts"].find_one()
    res = await client.put(
        url=f"/users/{username}",
        headers=headers,
        json={k: v for k, v in account_data.items() if k != "password"},
    )
    assert fails(res, None)
    assert e == await database.database["accounts"].find_one()


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
    account_data["username"] = account_datas[1]["username"]
    res = await client.put(
        url=f"/users/{username}",
        headers=headers,
        json=account_data,
    )
    assert fails(res, None)
    e = await database.database["accounts"].find_one()
    assert account_data["username"] == e["username"]
    e = await database.database["configurations"].find_one()
    assert account_data["username"] == e["username"]
    e = await database.database["access_tokens"].find_one()
    assert account_data["username"] == e["username"]


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
    await setup_account(client, account_datas[1]["username"], account_datas[1])
    account_data = copy.deepcopy(account_data)
    account_data["username"] = account_datas[1]["username"]
    res = await client.put(
        url=f"/users/{username}",
        headers=headers,
        json=account_data,
    )
    assert fails(res, errors.UsernameAlreadyTakenError)
    e = await database.database["accounts"].find_one(
        filter={"email_address": email_address},
    )
    assert username == e["username"]


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
    account_data["password"] = account_datas[1]["password"]
    res = await client.put(
        url=f"/users/{username}",
        headers=headers,
        json=account_data,
    )
    assert fails(res, None)
    e = await database.database["accounts"].find_one()
    assert auth.verify_password(account_data["password"], e["password_hash"])


@pytest.mark.skip(reason="todo")
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
    account_data["email_address"] = account_datas[1]["email_address"]
    res = await client.put(
        url=f"/users/{username}",
        headers=headers,
        json=account_data,
    )
    assert fails(res, errors.EmailAddressAlreadyTakenError)


########################################################################################
# Route: Delete User
########################################################################################


@pytest.mark.asyncio
async def test_deleting_existing_user(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    submissions,
    cleanup,
):
    """Test that all data is correctly wiped when a user is deleted."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, "simple", submissions[0])
    configuration = await survey.read(username, "simple")
    res = await client.delete(url=f"/users/{username}", headers=headers)
    assert fails(res, None)
    assert await database.database["accounts"].find_one() is None
    assert await database.database["access_tokens"].find_one() is None
    assert await database.database["configurations"].find_one() is None
    e = await survey.submissions_collection(configuration).find_one()
    assert e is None


########################################################################################
# Route: Read Surveys
########################################################################################


@pytest.mark.asyncio
async def test_reading_existing_surveys(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    configurations,
    cleanup,
):
    """Test that correct configurations of a specific user are returned."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_survey(client, headers, username, configurations[0])
    res = await client.get(url=f"/users/{username}/surveys", headers=headers)
    assert fails(res, None)
    assert len(res.json()) == 2
    assert {"next_identifier": 4, **configuration} in res.json()
    assert {"next_identifier": 2, **configurations[0]} in res.json()


@pytest.mark.asyncio
async def test_reading_nonexistent_surveys(
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
    res = await client.get(url=f"/users/{username}/surveys", headers=headers)
    assert fails(res, None)
    assert res.json() == []


########################################################################################
# Route: Read Survey
########################################################################################


@pytest.mark.asyncio
async def test_reading_existing_survey(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    cleanup,
):
    """Test that correct configuration is returned for an existing survey."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    res = await client.get(f"/users/{username}/surveys/simple")
    assert fails(res, None)
    assert res.json() == {"next_identifier": 4, **configuration}


@pytest.mark.asyncio
async def test_reading_nonexistent_survey(client, username):
    """Test that exception is raised when requesting a nonexistent survey."""
    res = await client.get(f"/users/{username}/surveys/simple")
    assert fails(res, errors.SurveyNotFoundError)


@pytest.mark.asyncio
async def test_reading_existing_survey_in_draft_mode(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    cleanup,
):
    """Test that exception is raised when requesting a survey in draft mode."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    configuration = copy.deepcopy(configuration)
    configuration["draft"] = True
    await setup_survey(client, headers, username, configuration)
    res = await client.get(f"/users/{username}/surveys/simple")
    assert fails(res, errors.SurveyNotFoundError)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_reading_existing_survey_outside_time_limits(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    cleanup,
):
    """Test only meta data is returned on request outside time limits."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    configuration = copy.deepcopy(configuration)
    configuration["end"] = configuration["start"]
    await setup_survey(client, headers, username, configuration)
    res = await client.get(f"/users/{username}/surveys/simple")
    assert fails(res, None)
    assert res.json() == {
        k: v for k, v in configuration.items() if k not in ["next_identifier", "fields"]
    }


########################################################################################
# route: create survey
########################################################################################


@pytest.mark.asyncio
async def test_creating_survey_with_valid_configuration(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    cleanup,
):
    """Test that survey is correctly created given a valid configuration."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    res = await setup_survey(client, headers, username, configuration)
    assert fails(res, None)
    e = await database.database["configurations"].find_one()
    assert e["username"] == username
    assert e["survey_name"] == "simple"


@pytest.mark.asyncio
async def test_creating_survey_with_invalid_configuration(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    invalid_configurations,
    cleanup,
):
    """Test that survey creation fails with an invalid configuration."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    configuration = invalid_configurations[0]
    res = await setup_survey(client, headers, username, configuration)
    assert fails(res, errors.InvalidSyntaxError)
    e = await database.database["configurations"].find_one()
    assert e is None


########################################################################################
# Route: Update Survey
########################################################################################


@pytest.mark.asyncio
async def test_updating_existing_survey_with_valid_update_configurations(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configurations,
    cleanup,
):
    """Test that survey is correctly updated given a chain of valid updates."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configurations[0])
    for configuration in configurations[1:]:
        res = await client.put(
            url=f"/users/{username}/surveys/complex",
            headers=headers,
            json=configuration,
        )
        assert fails(res, None)
        e = await database.database["configurations"].find_one()
        assert e["title"] == configuration["title"]
        assert e["description"] == configuration["description"]


@pytest.mark.asyncio
async def test_updating_existing_survey_with_invalid_update_configuration(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    cleanup,
):
    """Test that request is rejected when the update is not allowed."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    # different field type but same identifier
    c1 = copy.deepcopy(configuration)
    c1["fields"][0] = {**c1["fields"][1], "identifier": 0}
    # invalid new identifier
    c2 = copy.deepcopy(configuration)
    c2["fields"][0]["identifier"] = len(c2["fields"]) + 1
    # check for errors
    for x in [c1, c2]:
        res = await client.put(
            url=f"/users/{username}/surveys/simple",
            headers=headers,
            json=x,
        )
        assert fails(res, errors.InvalidSyntaxError)


@pytest.mark.asyncio
async def test_updating_nonexistent_survey_with_valid_update_configuration(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    cleanup,
):
    """Test that survey update fails when the survey does not exist."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    res = await client.put(
        url=f"/users/{username}/surveys/simple",
        headers=headers,
        json=configuration,
    )
    assert fails(res, errors.SurveyNotFoundError)
    e = await database.database["configurations"].find_one()
    assert e is None


@pytest.mark.asyncio
async def test_updating_survey_name_to_survey_name_not_in_use(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    cleanup,
):
    """Test that survey name is updated when it is not already used."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    configuration = copy.deepcopy(configuration)
    configuration["survey_name"] = "kangaroo"
    res = await client.put(
        url=f"/users/{username}/surveys/simple",
        headers=headers,
        json=configuration,
    )
    assert fails(res, None)
    e = await database.database["configurations"].find_one()
    assert e["survey_name"] == "kangaroo"


@pytest.mark.asyncio
async def test_updating_survey_name_to_survey_name_in_use(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    cleanup,
):
    """Test that survey name update fails if survey name is already in use."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    configuration = copy.deepcopy(configuration)
    configuration["survey_name"] = "kangaroo"
    await setup_survey(client, headers, username, configuration)
    res = await client.put(
        url=f"/users/{username}/surveys/simple",
        headers=headers,
        json=configuration,
    )
    assert fails(res, errors.SurveyNameAlreadyTakenError)
    e = await database.database["configurations"].find_one(
        filter={"survey_name": "simple"},
    )
    assert e is not None


########################################################################################
# Route: Delete Survey
########################################################################################


@pytest.mark.asyncio
async def test_deleting_existing_survey_with_existing_submissions(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    submissions,
    cleanup,
):
    """Test that a survey including all submissions is correctly deleted."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, "simple", submissions[0])
    configuration = await survey.read(username, "simple")
    res = await client.delete(
        url=f"/users/{username}/surveys/simple",
        headers=headers,
    )
    assert fails(res, None)
    assert await database.database["configurations"].find_one() is None
    e = await survey.submissions_collection(configuration).find_one()
    assert e is None


########################################################################################
# Route: Export Submissions
########################################################################################


@pytest.mark.asyncio
async def test_exporting_submissions_with_submissions(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configurations,
    submissionss,
    cleanup,
):
    """Test submissions export with intermediate configuration updates."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    base = f"/users/{username}/surveys/complex"

    def extract_identifiers(configuration):
        return {str(field["identifier"]) for field in configuration["fields"]}

    # initial creation and first export without update
    await setup_survey(client, headers, username, configurations[0])
    for submission in submissionss[0]:
        await setup_submission(client, username, "complex", submission)
    res = await client.get(url=f"{base}/submissions", headers=headers)
    assert fails(res, None)
    assert len(res.json()) == len(submissionss[0])
    identifiers = extract_identifiers(configurations[0])
    assert all([set(x.keys()) == identifiers for x in res.json()])

    # exports with intermediate updates
    counter = len(submissionss[0])
    for configuration, submissions in zip(configurations[1:], submissionss[1:]):
        res = await client.put(url=base, headers=headers, json=configuration)
        assert fails(res, None)
        for submission in submissions:
            await setup_submission(client, username, "complex", submission)
        res = await client.get(url=f"{base}/submissions", headers=headers)
        assert fails(res, None)
        counter += len(submissions)
        assert len(res.json()) == counter
        identifiers = extract_identifiers(configuration)
        assert all([set(x.keys()) == identifiers for x in res.json()])


@pytest.mark.asyncio
async def test_exporting_submissions_without_submissions(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    cleanup,
):
    """Test that empty list is returned when no submissions exist."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    res = await client.get(
        url=f"/users/{username}/surveys/simple/submissions",
        headers=headers,
    )
    assert fails(res, None)
    assert res.json() == []


########################################################################################
# Route: Create Submission
#
# It suffices here to test only one valid and one invalid submission, instead of all
# examples that we have, as the validation is tested on its own.
########################################################################################


@pytest.mark.asyncio
async def test_creating_submission(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    submissions,
    cleanup,
):
    """Test that submission works given a valid submission."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    res = await setup_submission(client, username, "simple", submissions[0])
    assert fails(res, None)
    configuration = await survey.read(username, "simple")
    e = await survey.submissions_collection(configuration).find_one()
    assert e["submission"] == submissions[0]


@pytest.mark.asyncio
async def test_creating_invalid_submission(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    invalid_submissions,
    cleanup,
):
    """Test that submit correctly fails given an invalid submissions."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    submission = invalid_submissions[0]
    res = await setup_submission(client, username, "simple", submission)
    assert fails(res, errors.InvalidSyntaxError)
    configuration = await survey.read(username, "simple")
    e = await survey.submissions_collection(configuration).find_one()
    assert e is None


########################################################################################
# Route: Reset Survey
########################################################################################


@pytest.mark.asyncio
async def test_resetting_survey_with_existing_submissions(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    submissions,
    cleanup,
):
    """Test that verified and unverified submissions are correctly deleted."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, "simple", submissions[0])
    configuration = await survey.read(username, "simple")
    res = await client.delete(
        url=f"/users/{username}/surveys/simple/submissions",
        headers=headers,
    )
    assert fails(res, None)
    assert await database.database["configurations"].find_one() is not None
    e = await survey.submissions_collection(configuration).find_one()
    assert e is None


########################################################################################
# Route: Verify Submission
########################################################################################


@pytest.mark.asyncio
async def test_verifying_valid_verification_token(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    submissions,
    cleanup,
):
    """Test submission is correctly verified given valid verification token."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, "simple", submissions[0])
    res = await client.post(
        url=f"/users/{username}/surveys/simple/verification",
        json={"verification_token": conftest.valid_token()},
    )
    assert fails(res, None)
    configuration = await survey.read(username, "simple")
    e = await survey.submissions_collection(configuration).find_one()
    assert e["verified"]


@pytest.mark.asyncio
async def test_verifying_invalid_verification_token(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    submissions,
    cleanup,
):
    """Test that request is rejected given an invalid verification token."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    await setup_submission(client, username, "simple", submissions[0])
    res = await client.post(
        url=f"/users/{username}/surveys/simple/verification",
        json={"verification_token": conftest.invalid_token()},
    )
    assert fails(res, errors.InvalidVerificationTokenError)
    configuration = await survey.read(username, "simple")
    e = await survey.submissions_collection(configuration).find_one()
    assert not e["verified"]


########################################################################################
# Route: Read Results
########################################################################################


@pytest.mark.asyncio
async def test_reading_results_with_submissions(
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
    """Test that aggregation works correctly even with intermediate updates."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    base = f"/users/{username}/surveys/complex"

    # initial creation and first aggregation without update
    await setup_survey(client, headers, username, configurations[0])
    for submission in submissionss[0]:
        await setup_submission(client, username, "complex", submission)
    res = await client.get(url=f"{base}/results", headers=headers)
    assert fails(res, None)
    assert res.json() == resultss[0]

    # aggregations with intermediate updates
    for i, configuration in enumerate(configurations[1:]):
        res = await client.put(url=base, headers=headers, json=configuration)
        assert fails(res, None)
        for submission in submissionss[i + 1]:
            await setup_submission(client, username, "complex", submission)
        res = await client.get(url=f"{base}/results", headers=headers)
        assert fails(res, None)
        assert res.json() == resultss[i + 1]


@pytest.mark.asyncio
async def test_reading_results_without_submissions(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    configuration,
    default_results,
    cleanup,
):
    """Test that aggregation works when no submissions have yet been made."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    headers = await setup_headers(client, account_data)
    await setup_survey(client, headers, username, configuration)
    res = await client.get(
        url=f"/users/{username}/surveys/simple/results",
        headers=headers,
    )
    assert fails(res, None)
    assert res.json() == default_results


########################################################################################
# Route: Create Access Token
########################################################################################


@pytest.mark.asyncio
async def test_creating_access_token_with_non_verified_account(
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
        url="/authentication",
        json={"identifier": username, "password": password},
    )
    assert fails(res, errors.AccountNotVerifiedError)


@pytest.mark.asyncio
async def test_creating_access_token_with_valid_identifier_and_password(
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
            url="/authentication",
            json={"identifier": identifier, "password": password},
        )
        assert fails(res, None)
        assert res.json().keys() == {"username", "access_token"}
        assert res.json()["username"] == username


@pytest.mark.asyncio
async def test_creating_access_token_with_valid_identifier(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    email_address,
    account_data,
    cleanup,
):
    """Test that password-less magic authentication works with valid identifier."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    # test with username as well as email address as identifier
    for identifier in [username, email_address]:
        res = await client.post(url="/authentication", json={"identifier": identifier})
        assert fails(res, None)
        assert res.json().keys() == {"username", "access_token"}
        assert res.json()["username"] == username


@pytest.mark.asyncio
async def test_creating_access_token_with_invalid_username(client, username, password):
    """Test that authentication fails for a user that does not exist."""
    res = await client.post(
        url="/authentication",
        json={"identifier": username, "password": password},
    )
    assert fails(res, errors.UserNotFoundError)


@pytest.mark.asyncio
async def test_creating_access_token_with_invalid_password(
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
        url="/authentication",
        json={"identifier": username, "password": "kangaroo"},
    )
    assert fails(res, errors.InvalidPasswordError)


########################################################################################
# Route: Verify Access Token
########################################################################################


@pytest.mark.asyncio
async def test_verifying_access_token_with_valid_verification_token(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    cleanup,
):
    """Test that magic login access token is only valid after email verification."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    res = await client.post(url="/authentication", json={"identifier": username})
    # check that first token is not activated yet
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    res = await client.get(f"/users/{username}", headers=headers)
    assert fails(res, errors.InvalidAccessTokenError)
    # check that first token works after email verification
    res = await client.put(
        url="/authentication",
        json={"verification_token": conftest.valid_token()},
    )
    assert fails(res, None)
    assert fails(await client.get(f"/users/{username}", headers=headers), None)
    # check that second token works after email verification
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    assert fails(await client.get(f"/users/{username}", headers=headers), None)


@pytest.mark.asyncio
async def test_verifying_access_token_with_invalid_verification_token(
    mock_email_sending,
    mock_token_generation,
    client,
    username,
    account_data,
    cleanup,
):
    """Test that access token verification fails with invalid verification token."""
    await setup_account(client, username, account_data)
    await setup_account_verification(client)
    res = await client.post(url="/authentication", json={"identifier": username})
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    res = await client.put(
        url="/authentication",
        json={"verification_token": conftest.invalid_token()},
    )
    assert fails(res, errors.InvalidVerificationTokenError())
    # check that access token is still not activated
    res = await client.get(f"/users/{username}", headers=headers)
    assert fails(res, errors.InvalidAccessTokenError)


########################################################################################
# Route: Delete Access Token
########################################################################################


@pytest.mark.asyncio
async def test_deleting_existing_access_token(
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
    res = await client.delete(url="/authentication", headers=headers)
    assert fails(res, None)
    assert await database.database["access_token"].find_one() is None
    # try changing account data with old access token
    res = await client.put(
        url=f"/users/{username}",
        headers=headers,
        json=account_data,
    )
    assert fails(res, errors.InvalidAccessTokenError)


########################################################################################
# Route: Verify Email Address
########################################################################################


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
    assert fails(res, None)
    e = await database.database["accounts"].find_one({"username": username})
    assert e["verified"]


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
        url=f"/verification",
        json={"verification_token": conftest.invalid_token()},
    )
    assert fails(res, errors.InvalidVerificationTokenError)
    e = await database.database["accounts"].find_one({"username": username})
    assert not e["verified"]


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
    assert fails(res, None)
    e = await database.database["accounts"].find_one({"username": username})
    assert e["verified"]
