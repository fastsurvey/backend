import os

from fastapi import FastAPI, Path, Query, Body, Form, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient, ASCENDING

from app.mailing import Letterbox
from app.account import AccountManager
from app.survey import SurveyManager
from app.cryptography import TokenManager


# check that required environment variables are set
assert all([
    os.getenv(var)
    for var
    in [
        'ENVIRONMENT',
        'FRONTEND_URL',
        'BACKEND_URL',
        'PUBLIC_RSA_KEY',
        'PRIVATE_RSA_KEY',
        'MONGODB_CONNECTION_STRING',
        'MAILGUN_API_KEY',
    ]
])


# development / production / testing environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
# MongoDB connection string
MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')


# connect to mongodb via pymongo
client = MongoClient(MONGODB_CONNECTION_STRING)
# get link to development / production / testing database
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
app = FastAPI()
# connect to mongodb via motor
client = AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
# get link to development / production / testing database
database = client[ENVIRONMENT]
# create email client
letterbox = Letterbox()
# create JWT manager
token_manager = TokenManager()
# instantiate survey manager
survey_manager = SurveyManager(database, letterbox, token_manager)
# instantiate account manager
account_manager = AccountManager(
    database,
    letterbox,
    token_manager,
    survey_manager,
)
# fastapi password bearer
oauth2_scheme = OAuth2PasswordBearer('/authentication')


@app.get(
    path='/users/{username}',
    responses={
        200: {
            'content': {
                'application/json': {
                    'example': {
                        'username': 'fastsurvey',
                        'email_address': 'info@fastsurvey.io',
                        'verified': True,
                    }
                }
            }
        }
    },
)
async def fetch_user(
        username: str = Path(..., description='The username of the user'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Fetch the given user's account data."""
    return await account_manager.fetch(username, access_token)


@app.post('/users/{username}')
async def create_user(
        username: str = Path(..., description='The username of the user'),
        email: str = Form(..., description='The users\'s email address'),
        password: str = Form(..., description='The account password'),
    ):
    """Create a new user with default account data."""
    await account_manager.create(username, email, password)


@app.put('/users/{username}')
async def update_user(
        username: str = Path(..., description='The username of the user'),
        account_data: dict = Body(..., description='The updated account data'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Update the given user's account data."""
    return await account_manager.update(username, account_data, access_token)


@app.delete('/users/{username}')
async def delete_user(
        username: str = Path(..., description='The username of the user'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Delete the user and all her surveys from the database."""
    return await account_manager.delete(username, access_token)


@app.get('/users/{username}/surveys')
async def fetch_configurations(
        username: str = Path(..., description='The username of the user'),
        skip: int = Query(0, description='Index of the first configuration'),
        limit: int = Query(10, description='Query limit; 0 means no limit'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Fetch the user's configurations sorted by the start date."""
    return await account_manager.fetch_configurations(
        username,
        skip,
        limit,
        access_token,
    )


@app.get('/users/{username}/surveys/{survey_name}')
async def fetch_configuration(
        username: str = Path(..., description='The username of the user'),
        survey_name: str = Path(..., description='The name of the survey'),
    ):
    """Fetch the configuration document of a given survey."""
    return await survey_manager.fetch(username, survey_name)


@app.post('/users/{username}/surveys/{survey_name}')
async def create_survey(
        username: str = Path(..., description='The username of the user'),
        survey_name: str = Path(..., description='The name of the survey'),
        configuration: dict = Body(..., description='The new configuration'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Create new survey with given configuration."""
    await survey_manager.create(
        username,
        survey_name,
        configuration,
        access_token,
    )


@app.put('/users/{username}/surveys/{survey_name}')
async def update_survey(
        username: str = Path(..., description='The username of the user'),
        survey_name: str = Path(..., description='The name of the survey'),
        configuration: dict = Body(..., description='Updated configuration'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Update survey with given configuration."""
    await survey_manager.update(
        username,
        survey_name,
        configuration,
        access_token,
    )


@app.delete('/users/{username}/surveys/{survey_name}')
async def delete_survey(
        username: str = Path(..., description='The username of the user'),
        survey_name: str = Path(..., description='The name of the survey'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Delete given survey including all its submissions and other data."""
    await survey_manager.delete(username, survey_name, access_token)


@app.post('/users/{username}/surveys/{survey_name}/submissions')
async def submit(
        username: str = Path(..., description='The username of the user'),
        survey_name: str = Path(..., description='The name of the survey'),
        submission: dict = Body(..., description='The user submission'),
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager._fetch(username, survey_name)
    return await survey.submit(submission)


@app.delete('/users/{username}/surveys/{survey_name}/submissions')
async def reset_survey(
        username: str = Path(..., description='The username of the user'),
        survey_name: str = Path(..., description='The name of the survey'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Reset a survey by delete all submission data including any results."""
    await survey_manager.reset(username, survey_name, access_token)


@app.get('/users/{username}/surveys/{survey_name}/verification/{token}')
async def verify(
        username: str = Path(..., description='The username of the user'),
        survey_name: str = Path(..., description='The name of the survey'),
        token: str = Path(..., description='The verification token'),
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager._fetch(username, survey_name)
    return await survey.verify(token)


@app.get('/users/{username}/surveys/{survey_name}/results')
async def aggregate(
        username: str = Path(..., description='The username of the user'),
        survey_name: str = Path(..., description='The name of the survey'),
    ):
    """Fetch the results of the given survey."""

    # TODO adapt result following authentication

    survey = await survey_manager._fetch(username, survey_name)
    return await survey.aggregate()


@app.post('/authentication')
async def authenticate(
        identifier: str = Form(..., description='The email or username'),
        password: str = Form(..., description='The account password'),
    ):
    return await account_manager.authenticate(identifier, password)


@app.post('/authentication/email-verification')
async def verify_email_address(
        token: str = Form(..., description='The account verification token'),
        password: str = Form(..., description='The account password'),
    ):
    return await account_manager.verify(token, password)
