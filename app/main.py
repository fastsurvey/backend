import fastapi
import fastapi.middleware.cors
import pydantic

import app.account as ac
import app.survey as sv
import app.documentation as docs
import app.cryptography.access as access
import app.settings as settings
import app.validation as validation


# create fastapi app
app = fastapi.FastAPI(
    title='FastSurvey',
    version='0.3.0',
    docs_url='/documentation/swagger',
    redoc_url='/documentation/redoc',
)
# configure cross-origin resource sharing
app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
# instantiate survey manager
survey_manager = sv.SurveyManager()
# instantiate account manager
account_manager = ac.AccountManager(survey_manager)


################################################################################
# Pydantic Type Definitions
################################################################################


class AccountData(pydantic.BaseModel):
    username: str
    email_address: str
    password: str


class AuthenticationCredentials(pydantic.BaseModel):
    identifier: str
    password: str


class VerificationCredentials(pydantic.BaseModel):
    verification_token: str
    password: str


################################################################################
# Routes
################################################################################


@app.get(**docs.SPECIFICATIONS['server_status'])
async def server_status():
    """Return some information about the server."""
    return dict(
        commit_sha=settings.COMMIT_SHA,
        branch_name=settings.BRANCH_NAME,
        start_time=settings.START_TIME,
    )


@app.get(**docs.SPECIFICATIONS['fetch_user'])
@access.authorize
async def fetch_user(
        access_token: str = docs.ARGUMENTS['access_token'],
        username: str = docs.ARGUMENTS['username'],
    ):
    """Fetch the given user's account data."""
    return await account_manager.fetch(username)


@app.post(**docs.SPECIFICATIONS['create_user'])
async def create_user(
        username: str = docs.ARGUMENTS['username'],
        account_data: validation.AccountData = docs.ARGUMENTS['account_data'],
    ):
    """Create a new user based on the given account data."""
    await account_manager.create(username, account_data)


@app.put(**docs.SPECIFICATIONS['update_user'])
@access.authorize
async def update_user(
        access_token: str = docs.ARGUMENTS['access_token'],
        username: str = docs.ARGUMENTS['username'],
        account_data: validation.AccountData = docs.ARGUMENTS['account_data'],
    ):
    """Update the given user's account data."""
    await account_manager.update(username, account_data)


@app.delete(**docs.SPECIFICATIONS['delete_user'])
@access.authorize
async def delete_user(
        access_token: str = docs.ARGUMENTS['access_token'],
        username: str = docs.ARGUMENTS['username'],
    ):
    """Delete the user and all their surveys from the database."""
    await account_manager.delete(username)


@app.get(**docs.SPECIFICATIONS['fetch_surveys'])
@access.authorize
async def fetch_surveys(
        access_token: str = docs.ARGUMENTS['access_token'],
        username: str = docs.ARGUMENTS['username'],
        skip: int = docs.ARGUMENTS['skip'],
        limit: int = docs.ARGUMENTS['limit'],
    ):
    """Fetch the user's survey configurations sorted by the start date.

    As this is a protected route, configurations of surveys that are in
    draft mode **are** returned.

    """
    return await account_manager.fetch_configurations(username, skip, limit)


@app.get(**docs.SPECIFICATIONS['fetch_survey'])
async def fetch_survey(
        username: str = docs.ARGUMENTS['username'],
        survey_name: str = docs.ARGUMENTS['survey_name'],
    ):
    """Fetch a survey configuration.

    As this is an unprotected route, configurations of surveys that are in
    draft mode **are not** returned.

    """
    return await survey_manager.fetch_configuration(
        username,
        survey_name,
        return_drafts=False,
    )


@app.post(**docs.SPECIFICATIONS['create_survey'])
@access.authorize
async def create_survey(
        access_token: str = docs.ARGUMENTS['access_token'],
        username: str = docs.ARGUMENTS['username'],
        survey_name: str = docs.ARGUMENTS['survey_name'],
        configuration: dict = docs.ARGUMENTS['configuration'],
    ):
    """Create new survey with given configuration."""
    await survey_manager.create(username, survey_name, configuration)


@app.put(**docs.SPECIFICATIONS['update_survey'])
@access.authorize
async def update_survey(
        access_token: str = docs.ARGUMENTS['access_token'],
        username: str = docs.ARGUMENTS['username'],
        survey_name: str = docs.ARGUMENTS['survey_name'],
        configuration: dict = docs.ARGUMENTS['configuration'],
    ):
    """Update survey with given configuration."""
    await survey_manager.update(username, survey_name, configuration)


@app.delete(**docs.SPECIFICATIONS['reset_survey'])
@access.authorize
async def reset_survey(
        access_token: str = docs.ARGUMENTS['access_token'],
        username: str = docs.ARGUMENTS['username'],
        survey_name: str = docs.ARGUMENTS['survey_name'],
    ):
    """Reset a survey by deleting all submission data including any results."""
    await survey_manager.reset(username, survey_name)


@app.delete(**docs.SPECIFICATIONS['delete_survey'])
@access.authorize
async def delete_survey(
        access_token: str = docs.ARGUMENTS['access_token'],
        username: str = docs.ARGUMENTS['username'],
        survey_name: str = docs.ARGUMENTS['survey_name'],
    ):
    """Delete given survey including all its submissions and other data."""
    await survey_manager.delete(username, survey_name)


@app.post(**docs.SPECIFICATIONS['create_submission'])
async def create_submission(
        username: str = docs.ARGUMENTS['username'],
        survey_name: str = docs.ARGUMENTS['survey_name'],
        submission: dict = docs.ARGUMENTS['submission'],
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager.fetch(
        username,
        survey_name,
        return_drafts=False,
    )
    return await survey.submit(submission)


@app.get(**docs.SPECIFICATIONS['verify_submission'])
async def verify_submission(
        username: str = docs.ARGUMENTS['username'],
        survey_name: str = docs.ARGUMENTS['survey_name'],
        verification_token: str = docs.ARGUMENTS['verification_token'],
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager.fetch(
        username,
        survey_name,
        return_drafts=False,
    )
    return await survey.verify(verification_token)


@app.get(**docs.SPECIFICATIONS['fetch_results'])
@access.authorize
async def fetch_results(
        access_token: str = docs.ARGUMENTS['access_token'],
        username: str = docs.ARGUMENTS['username'],
        survey_name: str = docs.ARGUMENTS['survey_name'],
    ):
    """Fetch the results of the given survey."""
    survey = await survey_manager.fetch(username, survey_name)
    return await survey.aggregate()


@app.get(**docs.SPECIFICATIONS['decode_access_token'])
async def decode_access_token(
        access_token: str = docs.ARGUMENTS['access_token'],
    ):
    """Decode the given access token and return the contained username."""
    return access.decode(access_token)


@app.post(**docs.SPECIFICATIONS['generate_access_token'])
async def generate_access_token(
        authentication_credentials: AuthenticationCredentials = (
            docs.ARGUMENTS['authentication_credentials']
        ),
    ):
    """Generate a JWT access token containing the user's username."""
    return await account_manager.authenticate(
        authentication_credentials.identifier,
        authentication_credentials.password,
    )


@app.put(**docs.SPECIFICATIONS['refresh_access_token'])
async def refresh_access_token(
        access_token: str = docs.ARGUMENTS['access_token'],
    ):
    """Generate a new access token with a refreshed expiration time."""
    return access.generate(access.decode(access_token))


@app.post(**docs.SPECIFICATIONS['verify_email_address'])
async def verify_email_address(
        verification_credentials: VerificationCredentials = (
            docs.ARGUMENTS['verification_credentials']
        ),
    ):
    """Verify an email address given the verification token sent via email."""
    return await account_manager.verify(
        verification_credentials.verification_token,
        verification_credentials.password,
    )
