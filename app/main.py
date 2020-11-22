import os

from fastapi import FastAPI, Path, Query, Body, Form, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.mailing import Letterbox
from app.account import AccountManager
from app.survey import SurveyManager


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


# create fastapi app
app = FastAPI()
# connect to mongodb via pymongo and motor
motor_client = AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
# get link to development / production / testing database
database = motor_client[ENVIRONMENT]
# create email client
letterbox = Letterbox()
# instantiate survey manager
survey_manager = SurveyManager(database, letterbox)
# instantiate admin acount manager
account_manager = await AccountManager(database, survey_manager, letterbox)


@app.get('/admins/{admin_name}')
async def fetch_admin(
        admin_name: str = Path(..., description='The username of the admin'),
    ):
    """Fetch the given admin's account data."""
    raise HTTPException(401, 'authentication not yet implemented')
    # TODO check authentication
    return await account_manager.fetch(admin_name)


@app.post('/admins/{admin_name}')
async def create_admin(
        admin_name: str = Path(..., description='The username of the admin'),
        email: str = Form(..., description='The admin\'s email address'),
        password: str = Form(..., description='The account password'),
    ):
    """Create a new admin with default account data."""
    return await account_manager.create(admin_name, email, password)


@app.put('/admins/{admin_name}')
async def update_admin(
        admin_name: str = Path(..., description='The username of the admin'),
        account_data: dict = Body(..., description='The updated account data'),
    ):
    """Update the given admin's account data."""
    raise HTTPException(401, 'authentication not yet implemented')
    # TODO check authentication
    return await account_manager.update(admin_name, account_data)


@app.delete('/admins/{admin_name}')
async def delete_admin(
        admin_name: str = Path(..., description='The username of the admin'),
    ):
    """Delete the admin and all her surveys from the database."""
    raise HTTPException(401, 'authentication not yet implemented')
    # TODO check authentication
    return await account_manager.delete(admin_name)


@app.get('/admins/{admin_name}/surveys')
async def fetch_surveys(
        admin_name: str = Path(..., description='The username of the admin'),
        skip: int = Query(0, description='Index of the first configuration'),
        limit: int = Query(10, description='Query limit; 0 means no limit'),
    ):
    """Fetch the admin's configurations sorted by the start date."""
    raise HTTPException(401, 'authentication not yet implemented')
    # TODO check authentication
    return await survey_manager.fetch_multiple(admin_name, skip, limit)


@app.get('/admins/{admin_name}/surveys/{survey_name}')
async def fetch_survey(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
    ):
    """Fetch the configuration document of the given survey."""
    survey = await survey_manager.fetch(admin_name, survey_name)
    return survey.configuration


@app.post('/admins/{admin_name}/surveys/{survey_name}')
async def create_survey(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        configuration: dict = Body(..., description='The new configuration'),
    ):
    """Create new survey with given configuration."""
    raise HTTPException(401, 'authentication not yet implemented')
    # TODO check authentication
    await survey_manager.create(admin_name, survey_name, configuration)


@app.put('/admins/{admin_name}/surveys/{survey_name}')
async def update_survey(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        configuration: dict = Body(..., description='Updated configuration'),
    ):
    """Update survey with given configuration."""
    raise HTTPException(401, 'authentication not yet implemented')
    # TODO check authentication
    await survey_manager.update(admin_name, survey_name, configuration)


@app.delete('/admins/{admin_name}/surveys/{survey_name}')
async def delete_survey(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
    ):
    """Delete given survey and all its data (submissions, results, ...)."""
    raise HTTPException(401, 'authentication not yet implemented')
    # TODO check authentication
    await survey_manager.delete(admin_name, survey_name)


@app.post('/admins/{admin_name}/surveys/{survey_name}/submission')
async def submit(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        submission: dict = Body(..., description='The user submission'),
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager.fetch(admin_name, survey_name)
    return await survey.submit(submission)


@app.get('/admins/{admin_name}/surveys/{survey_name}/verification/{token}')
async def verify(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
        token: str = Path(..., description='The verification token'),
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager.fetch(admin_name, survey_name)
    return await survey.verify(token)


@app.get('/admins/{admin_name}/surveys/{survey_name}/results')
async def aggregate(
        admin_name: str = Path(..., description='The username of the admin'),
        survey_name: str = Path(..., description='The name of the survey'),
    ):
    """Fetch the results of the given survey."""
    # TODO adapt result following authentication
    survey = await survey_manager.fetch(admin_name, survey_name)
    return await survey.aggregate()
