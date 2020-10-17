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
async def get_admin(
        admin_name: str = Path(
            ...,
            description='The name of the admin',
        ),
        start: int = Query(
            0,
            description='The index of the first configuration to be fetched',
        ),
        end: int = Query(
            0,
            description='The index of the last configuration plus one',
        )
    ):
    """Fetch data about the given admin and optionally her configurations."""
    # TODO check authentication
    return await admin_manager.fetch(admin_name, start, end)


@app.get('/{admin_name}/{survey_name}')
async def get_survey(
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
async def post_survey(
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
    raise HTTPException(501, 'not implemented')


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
