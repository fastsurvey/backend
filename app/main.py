import os
import fastapi
import fastapi.middleware.cors
import motor.motor_asyncio
import pymongo
import pydantic

import app.email as email
import app.account as ac
import app.survey as sv
import app.documentation as docs
import app.cryptography.access as access


# check that required environment variables are set
envs = [
    'ENVIRONMENT',
    'FRONTEND_URL',
    'BACKEND_URL',
    'PUBLIC_RSA_KEY',
    'PRIVATE_RSA_KEY',
    'MONGODB_CONNECTION_STRING',
    'MAILGUN_API_KEY',
]
for env in envs:
    assert os.getenv(env), f'environment variable {env} not set'


# development / production / testing environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
# MongoDB connection string
MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')


# connect to mongodb via pymongo
client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
# get link to development / production / testing database via pymongo
database = client[ENVIRONMENT]
# set up database indices synchronously via pymongo
database['configurations'].create_index(
    keys=[('username', pymongo.ASCENDING), ('survey_name', pymongo.ASCENDING)],
    name='username_survey_name_index',
    unique=True,
)
database['accounts'].create_index(
    keys='email_address',
    name='email_address_index',
    unique=True,
)
database['accounts'].create_index(
    keys='verification_token',
    name='verification_token_index',
    unique=True,
)
database['accounts'].create_index(
    keys='creation_time',
    name='creation_time_index',
    expireAfterSeconds=10*60,  # delete draft accounts after 10 mins
    partialFilterExpression={'verified': {'$eq': False}},
)


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
# connect to mongodb via motor
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
# get link to development / production / testing database via motor
database = client[ENVIRONMENT]
# create email client
letterbox = email.Letterbox()
# instantiate survey manager
survey_manager = sv.SurveyManager(database, letterbox)
# instantiate account manager
account_manager = ac.AccountManager(database, letterbox, survey_manager)


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
    token: str
    password: str


################################################################################
# Routes
################################################################################


@app.get(**docs.specifications['fetch_user'])
async def fetch_user(
        username: str = docs.arguments['username'],
        access_token: str = docs.arguments['access_token'],
    ):
    """Fetch the given user's account data."""
    return await account_manager.fetch(username, access_token)


@app.post(**docs.specifications['create_user'])
async def create_user(
        username: str = docs.arguments['username'],
        account_data: dict = docs.arguments['account_data'],
    ):
    """Create a new user with default account data."""
    await account_manager.create(username, account_data)


@app.put(**docs.specifications['update_user'])
async def update_user(
        username: str = docs.arguments['username'],
        account_data: dict = docs.arguments['account_data'],
        access_token: str = docs.arguments['access_token'],
    ):
    """Update the given user's account data."""
    await account_manager.update(username, access_token, account_data)


@app.delete(**docs.specifications['delete_user'])
async def delete_user(
        username: str = docs.arguments['username'],
        access_token: str = docs.arguments['access_token'],
    ):
    """Delete the user and all her surveys from the database."""
    await account_manager.delete(username, access_token)


@app.get(**docs.specifications['fetch_surveys'])
async def fetch_surveys(
        username: str = docs.arguments['username'],
        skip: int = docs.arguments['skip'],
        limit: int = docs.arguments['limit'],
        access_token: str = docs.arguments['access_token'],
    ):
    """Fetch the user's survey configurations sorted by the start date."""
    return await account_manager.fetch_configurations(
        username,
        access_token,
        skip,
        limit,
    )


@app.get(**docs.specifications['fetch_survey'])
async def fetch_survey(
        username: str = docs.arguments['username'],
        survey_name: str = docs.arguments['survey_name'],
    ):
    """Fetch a survey configuration."""
    return await survey_manager.fetch_configuration(username, survey_name)


@app.post(**docs.specifications['create_survey'])
async def create_survey(
        username: str = docs.arguments['username'],
        survey_name: str = docs.arguments['survey_name'],
        configuration: dict = docs.arguments['configuration'],
        access_token: str = docs.arguments['access_token'],
    ):
    """Create new survey with given configuration."""
    await survey_manager.create(
        username,
        access_token,
        survey_name,
        configuration,
    )


@app.put(**docs.specifications['update_survey'])
async def update_survey(
        username: str = docs.arguments['username'],
        survey_name: str = docs.arguments['survey_name'],
        configuration: dict = docs.arguments['configuration'],
        access_token: str = docs.arguments['access_token'],
    ):
    """Update survey with given configuration."""
    await survey_manager.update(
        username,
        access_token,
        survey_name,
        configuration,
    )


@app.delete(**docs.specifications['delete_survey'])
async def delete_survey(
        username: str = docs.arguments['username'],
        survey_name: str = docs.arguments['survey_name'],
        access_token: str = docs.arguments['access_token'],
    ):
    """Delete given survey including all its submissions and other data."""
    await survey_manager.delete(username, access_token, survey_name)


@app.post(**docs.specifications['create_submission'])
async def create_submission(
        username: str = docs.arguments['username'],
        survey_name: str = docs.arguments['survey_name'],
        submission: dict = docs.arguments['submission'],
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager.fetch(username, survey_name)
    return await survey.submit(submission)


@app.delete(**docs.specifications['reset_survey'])
async def reset_survey(
        username: str = docs.arguments['username'],
        survey_name: str = docs.arguments['survey_name'],
        access_token: str = docs.arguments['access_token'],
    ):
    """Reset a survey by deleting all submission data including any results."""
    await survey_manager.reset(username, access_token, survey_name)


@app.get(**docs.specifications['verify_submission'])
async def verify_submission(
        username: str = docs.arguments['username'],
        survey_name: str = docs.arguments['survey_name'],
        token: str = docs.arguments['token'],
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager.fetch(username, survey_name)
    return await survey.verify(token)


@app.get(**docs.specifications['fetch_results'])
async def fetch_results(
        username: str = docs.arguments['username'],
        survey_name: str = docs.arguments['survey_name'],
    ):
    """Fetch the results of the given survey."""

    # TODO adapt result following authentication

    survey = await survey_manager.fetch(username, survey_name)
    return await survey.aggregate()


@app.get(**docs.specifications['decode_access_token'])
async def decode_access_token(
        access_token: str = docs.arguments['access_token'],
    ):
    return access.decode(access_token)


@app.post(**docs.specifications['generate_access_token'])
async def generate_access_token(
        authentication_credentials: AuthenticationCredentials = (
            docs.arguments['authentication_credentials']
        ),
    ):
    return await account_manager.authenticate(
        authentication_credentials['identifier'],
        authentication_credentials['password'],
    )


@app.post(**docs.specifications['verify_email_address'])
async def verify_email_address(
        verification_credentials: VerificationCredentials = (
            docs.arguments['verification_credentials']
        ),
    ):
    return await account_manager.verify(
        verification_credentials['token'],
        verification_credentials['password'],
    )
