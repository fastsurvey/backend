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
    keys=[('admin_name', ASCENDING), ('survey_name', ASCENDING)],
    name='admin_name_survey_name_index',
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
# instantiate admin acount manager
account_manager = AccountManager(
    database,
    letterbox,
    token_manager,
    survey_manager,
)
# fastapi password bearer
oauth2_scheme = OAuth2PasswordBearer('/authentication')


@app.get('/admins/{admin_name}')
async def fetch_admin(
        admin_name: str = Path(..., description='The username of the admin'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Fetch the given admin's account data."""
    return await account_manager.fetch(admin_name, access_token)


@app.post('/admins/{admin_name}')
async def create_admin(
        admin_name: str = Path(..., description='The username of the admin'),
        email: str = Form(..., description='The admin\'s email address'),
        password: str = Form(..., description='The account password'),
    ):
    """Create a new admin with default account data."""
    await account_manager.create(admin_name, email, password)


@app.put('/admins/{admin_name}')
async def update_admin(
        admin_name: str = Path(..., description='The username of the admin'),
        account_data: dict = Body(..., description='The updated account data'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Update the given admin's account data."""
    return await account_manager.update(admin_name, account_data, access_token)


@app.delete('/admins/{admin_name}')
async def delete_admin(
        admin_name: str = Path(..., description='The username of the admin'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Delete the admin and all her surveys from the database."""
    return await account_manager.delete(admin_name, access_token)


@app.get('/admins/{admin_name}/surveys')
async def fetch_configurations(
        admin_name: str = Path(..., description='The username of the admin'),
        skip: int = Query(0, description='Index of the first configuration'),
        limit: int = Query(10, description='Query limit; 0 means no limit'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Fetch the admin's configurations sorted by the start date."""
    return await account_manager.fetch_configurations(
        admin_name,
        skip,
        limit,
        access_token,
    )


@app.get('/admins/{admin_name}/surveys/{survey_name}')
async def fetch_configuration(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
    ):
    """Fetch the configuration document of a given survey."""
    return await survey_manager.fetch(admin_name, survey_name)


@app.post('/admins/{admin_name}/surveys/{survey_name}')
async def create_survey(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        configuration: dict = Body(..., description='The new configuration'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Create new survey with given configuration."""
    await survey_manager.create(
        admin_name,
        survey_name,
        configuration,
        access_token,
    )


@app.put('/admins/{admin_name}/surveys/{survey_name}')
async def update_survey(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        configuration: dict = Body(..., description='Updated configuration'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Update survey with given configuration."""
    await survey_manager.update(
        admin_name,
        survey_name,
        configuration,
        access_token,
    )


@app.delete('/admins/{admin_name}/surveys/{survey_name}')
async def delete_survey(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Delete given survey including all its submissions and other data."""
    await survey_manager.delete(admin_name, survey_name, access_token)


@app.post('/admins/{admin_name}/surveys/{survey_name}/submissions')
async def submit(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        submission: dict = Body(..., description='The user submission'),
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager._fetch(admin_name, survey_name)
    return await survey.submit(submission)


@app.delete('/admins/{admin_name}/surveys/{survey_name}/submissions')
async def reset_survey(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Reset a survey by delete all submission data including any results."""
    await survey_manager.reset(admin_name, survey_name, access_token)


@app.get('/admins/{admin_name}/surveys/{survey_name}/verification/{token}')
async def verify(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        token: str = Path(..., description='The verification token'),
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager._fetch(admin_name, survey_name)
    return await survey.verify(token)


@app.get('/admins/{admin_name}/surveys/{survey_name}/results')
async def aggregate(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
    ):
    """Fetch the results of the given survey."""

    # TODO adapt result following authentication

    survey = await survey_manager._fetch(admin_name, survey_name)
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
