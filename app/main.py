import os


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


from fastapi import FastAPI, Path, Query, Body, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient, ASCENDING

from app.mailing import Letterbox
from app.account import AccountManager
from app.survey import SurveyManager
from app.cryptography import JWTManager
from app.documentation import specifications, parameters


# development / production / testing environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
# MongoDB connection string
MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')


# connect to mongodb via pymongo
client = MongoClient(MONGODB_CONNECTION_STRING)
# get link to development / production / testing database via pymongo
database = client[ENVIRONMENT]
# set up database indices synchronously via pymongo
database['configurations'].create_index(
    keys=[('username', ASCENDING), ('survey_name', ASCENDING)],
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
app = FastAPI(
    title='FastSurvey',
    version='0.3.0',
    docs_url='/documentation/swagger',
    redoc_url='/documentation/redoc',
)
# configure cross-origin resource sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
# connect to mongodb via motor
client = AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
# get link to development / production / testing database via motor
database = client[ENVIRONMENT]
# create email client
letterbox = Letterbox()
# create JWT manager
jwt_manager = JWTManager()
# instantiate survey manager
survey_manager = SurveyManager(database, letterbox, jwt_manager)
# instantiate account manager
account_manager = AccountManager(
    database,
    letterbox,
    jwt_manager,
    survey_manager,
)
# fastapi password bearer
oauth2_scheme = OAuth2PasswordBearer('/authentication')


@app.get(**specifications['fetch_user'])
async def fetch_user(
        username: str = Path(..., **parameters['username']),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Fetch the given user's account data."""
    return await account_manager.fetch(username, access_token)


@app.post(**specifications['create_user'])
async def create_user(
        username: str = Path(..., **parameters['username']),
        email: str = Form(..., **parameters['email']),
        password: str = Form(..., **parameters['password']),
    ):
    """Create a new user with default account data."""
    await account_manager.create(username, email, password)


@app.put(**specifications['update_user'])
async def update_user(
        username: str = Path(..., **parameters['username']),
        account_data: dict = Body(..., **parameters['account_data']),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Update the given user's account data."""
    await account_manager.update(username, account_data, access_token)


@app.delete(**specifications['delete_user'])
async def delete_user(
        username: str = Path(..., **parameters['username']),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Delete the user and all her surveys from the database."""
    await account_manager.delete(username, access_token)


@app.get(**specifications['fetch_surveys'])
async def fetch_surveys(
        username: str = Path(..., **parameters['username']),
        skip: int = Query(0, **parameters['skip']),
        limit: int = Query(10, **parameters['limit']),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Fetch the user's survey configurations sorted by the start date."""
    return await account_manager.fetch_configurations(
        username,
        skip,
        limit,
        access_token,
    )


@app.get(**specifications['fetch_survey'])
async def fetch_survey(
        username: str = Path(..., **parameters['username']),
        survey_name: str = Path(..., **parameters['survey_name']),
    ):
    """Fetch a survey configuration."""
    return await survey_manager.fetch(username, survey_name)


@app.post(**specifications['create_survey'])
async def create_survey(
        username: str = Path(..., **parameters['username']),
        survey_name: str = Path(..., **parameters['survey_name']),
        configuration: dict = Body(..., **parameters['configuration']),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Create new survey with given configuration."""
    await survey_manager.create(
        username,
        survey_name,
        configuration,
        access_token,
    )


@app.put(**specifications['update_survey'])
async def update_survey(
        username: str = Path(..., **parameters['username']),
        survey_name: str = Path(..., **parameters['survey_name']),
        configuration: dict = Body(..., **parameters['configuration']),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Update survey with given configuration."""
    await survey_manager.update(
        username,
        survey_name,
        configuration,
        access_token,
    )


@app.delete(**specifications['delete_survey'])
async def delete_survey(
        username: str = Path(..., **parameters['username']),
        survey_name: str = Path(..., **parameters['survey_name']),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Delete given survey including all its submissions and other data."""
    await survey_manager.delete(username, survey_name, access_token)


@app.post(**specifications['create_submission'])
async def create_submission(
        username: str = Path(..., **parameters['username']),
        survey_name: str = Path(..., **parameters['survey_name']),
        submission: dict = Body(..., **parameters['submission']),
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager._fetch(username, survey_name)
    return await survey.submit(submission)


@app.delete(**specifications['reset_survey'])
async def reset_survey(
        username: str = Path(..., **parameters['username']),
        survey_name: str = Path(..., **parameters['survey_name']),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Reset a survey by deleting all submission data including any results."""
    await survey_manager.reset(username, survey_name, access_token)


@app.get(**specifications['verify_submission'])
async def verify_submission(
        username: str = Path(..., **parameters['username']),
        survey_name: str = Path(..., **parameters['survey_name']),
        token: str = Path(..., **parameters['token']),
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager._fetch(username, survey_name)
    return await survey.verify(token)


@app.get(**specifications['fetch_results'])
async def fetch_results(
        username: str = Path(..., **parameters['username']),
        survey_name: str = Path(..., **parameters['survey_name']),
    ):
    """Fetch the results of the given survey."""

    # TODO adapt result following authentication

    survey = await survey_manager._fetch(username, survey_name)
    return await survey.aggregate()


@app.get(**specifications['decode_access_token'])
async def decode_access_token(
        access_token: str = Depends(oauth2_scheme),
    ):

    # TODO adapt decode function so we get nice HTTPExceptions on fail

    return jwt_manager.decode(access_token)


@app.post(**specifications['generate_access_token'])
async def generate_access_token(
        identifier: str = Form(..., **parameters['identifier']),
        password: str = Form(..., **parameters['password']),
    ):
    return await account_manager.authenticate(identifier, password)


@app.post(**specifications['verify_email_address'])
async def verify_email_address(
        token: str = Form(..., **parameters['token']),
        password: str = Form(..., **parameters['password']),
    ):
    return await account_manager.verify(token, password)
