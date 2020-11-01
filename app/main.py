import os

from fastapi import FastAPI, Path, Query, Body, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.mailing import Letterbox
from app.admin import AdminManager
from app.survey import SurveyManager


# development / production / testing environment
ENV = os.getenv('ENV')
# MongoDB connection string
MDBCS = os.getenv('MDBCS')


# create fastapi app
app = FastAPI()
# connect to mongodb via pymongo and motor
motor_client = AsyncIOMotorClient(MDBCS)
# get link to development / production / testing database
database = motor_client[ENV]
# create email client
letterbox = Letterbox()
# instantiate survey manager
survey_manager = SurveyManager(database, letterbox)
# instantiate admin manager
admin_manager = AdminManager(database, survey_manager)


@app.get('/admins/{admin_name}')
async def fetch_admin(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
    ):
    """Fetch the given admin's account data."""
    # TODO check authentication
    return await admin_manager.fetch(admin_name)


@app.post('/admins/{admin_name}')
async def create_admin(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        account_data: dict = Body(
            ...,
            description='The settings and other account data',
        ),
    ):
    """Create a new admin with given account data."""
    # TODO check authentication
    return await admin_manager.create(admin_name, account_data)


@app.put('/admins/{admin_name}')
async def update_admin(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        account_data: dict = Body(
            ...,
            description='The updated account data',
        ),
    ):
    """Update the given admin's account data."""
    # TODO check authentication
    return await admin_manager.update(admin_name, account_data)


@app.delete('/admins/{admin_name}')
async def delete_admin(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
    ):
    """Delete the admin and all her surveys from the database."""
    # TODO check authentication
    return await admin_manager.delete(admin_name)


@app.get('/admins/{admin_name}/surveys')
async def fetch_surveys(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        skip: int = Query(
            0,
            description='The index of the first configuration to be fetched',
        ),
        limit: int = Query(
            10,
            description='The maximum number of results, or 0 for no limit',
        )
    ):
    """Fetch the admin's configurations sorted by the start date."""
    # TODO check authentication
    return await admin_manager.fetch_configurations(admin_name, skip, limit)


@app.get('/admins/{admin_name}/surveys/{survey_name}')
async def fetch_survey(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey_name: str = Path(
            ...,
            description='The name of the survey',
        ),
    ):
    """Fetch the configuration document of the given survey."""
    survey = await survey_manager.fetch(admin_name, survey_name)
    return survey.configuration


@app.post('/admins/{admin_name}/surveys/{survey_name}')
async def create_survey(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey_name: str = Path(
            ...,
            description='The name of the survey',
        ),
        configuration: dict = Body(
            ...,
            description='The configuration for the new survey',
        ),
    ):
    """Create new survey with given configuration."""
    # TODO check authentication
    await survey_manager.create(admin_name, survey_name, configuration)


@app.put('/admins/{admin_name}/surveys/{survey_name}')
async def update_survey(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey_name: str = Path(
            ...,
            description='The name of the survey',
        ),
        configuration: dict = Body(
            ...,
            description='The updated configuration',
        ),
    ):
    """Update survey with given configuration."""
    # TODO check authentication
    await survey_manager.update(admin_name, survey_name, configuration)


@app.delete('/admins/{admin_name}/surveys/{survey_name}')
async def delete_survey(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey_name: str = Path(
            ...,
            description='The name of the survey',
        ),
    ):
    """Delete given survey and all its data (submissions, results, ...)."""
    # TODO check authentication
    await survey_manager.delete(admin_name, survey_name)


@app.post('/admins/{admin_name}/surveys/{survey_name}/submission')
async def submit(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey_name: str = Path(
            ...,
            description='The name of the survey',
        ),
        submission: dict = Body(
            ...,
            description='The user submission for the survey',
        ),
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager.fetch(admin_name, survey_name)
    return await survey.submit(submission)


@app.get('/admins/{admin_name}/surveys/{survey_name}/verification/{token}')
async def verify(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey_name: str = Path(
            ...,
            description='The name of the survey',
        ),
        token: str = Path(
            ...,
            description='The verification token',
        ),
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager.fetch(admin_name, survey_name)
    return await survey.verify(token)


@app.get('/admins/{admin_name}/surveys/{survey_name}/results')
async def aggregate(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey_name: str = Path(
            ...,
            description='The name of the survey',
        ),
    ):
    """Fetch the results of the given survey."""
    # TODO adapt result following authentication
    survey = await survey_manager.fetch(admin_name, survey_name)
    return await survey.aggregate()
