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
# instantiate admin manager
admin_manager = AdminManager(database)
# instantiate survey manager
survey_manager = SurveyManager(database, letterbox)


@app.get('/{admin_name}')
async def fetch_admin_account(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
    ):
    """Fetch the given admin's account data."""
    # TODO check authentication
    return await admin_manager.fetch_account(admin_name)


@app.post('/{admin_name}')
async def create_admin_account(
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
    raise HTTPException(501, 'not implemented')


@app.put('/{admin_name}')
async def update_admin_account(
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
    raise HTTPException(501, 'not implemented')


@app.delete('/{admin_name}')
async def delete_admin_account(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
    ):
    """Delete the admin and all her surveys from the database."""
    # TODO check authentication
    raise HTTPException(501, 'not implemented')


@app.get('/{admin_name}/configurations')
async def fetch_admin_configurations(
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


@app.get('/{admin_name}/{survey_name}')
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


@app.post('/{admin_name}/{survey_name}')
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
    await survey_manager.update(admin_name, survey_name, configuration)


@app.put('/{admin_name}/{survey_name}')
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


@app.delete('/{admin_name}/{survey_name}')
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
    raise HTTPException(501, 'not implemented')


@app.post('/{admin_name}/{survey_name}/submission')
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


@app.get('/{admin_name}/{survey_name}/verification/{token}')
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


@app.get('/{admin_name}/{survey_name}/results')
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
    survey = await survey_manager.fetch(admin_name, survey_name)
    return await survey.aggregate()
