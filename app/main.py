import os

from fastapi import FastAPI, Path, Body, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from postmarker.core import PostmarkClient

from app.survey import SurveyManager


# dev / production environment
ENV = os.getenv('ENV')
# MongoDB connection string
MDBCS = os.getenv('MDBCS')
# Postmark dev / production server token
PMST = os.getenv('DPMST' if ENV == 'development' else 'PPMST')


# create fastapi app
app = FastAPI()
# connect to mongodb via pymongo and motor
motor_client = AsyncIOMotorClient(MDBCS)
# get link to dev / production database
database = motor_client[ENV]
# connect to postmark
postmark = PostmarkClient(server_token=PMST)
# instantiate survey manager
survey_manager = SurveyManager(database, postmark)


@app.get('/', tags=['status'])
async def status():
    """Verify if database and mailing services are operational."""
    status = {'database': 'UP', 'mailing': 'UP'}
    try:
        await motor_client.server_info()
    except:
        status['database'] = 'DOWN'
    try:
        status['mailing'] = postmark.status.get()['status']
    except:
        status['mailing'] = 'DOWN'
    return status


@app.get('/{admin}/{survey}', tags=['survey'])
async def fetch(
        admin: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey: str = Path(
            ...,
            description='The name of the survey',
        ),
    ):
    """Fetch the configuration document of the given survey."""
    survey = await survey_manager.get(admin, survey)
    return survey.configuration


@app.post('/{admin}/{survey}/submit', tags=['survey'])
async def submit(
        admin: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey: str = Path(
            ...,
            description='The name of the survey',
        ),
        submission: dict = Body(
            ...,
            description='The user submission for the survey',
        )
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager.get(admin, survey)
    return await survey.submit(submission)


@app.get('/{admin}/{survey}/verify/{token}', tags=['survey'])
async def verify(
        admin: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey: str = Path(
            ...,
            description='The name of the survey',
        ),
        token: str = Path(
            ...,
            description='The verification token',
        ),
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager.get(admin, survey)
    return await survey.verify(token)


@app.get('/{admin}/{survey}/results', tags=['survey'])
async def aggregate(
        admin: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey: str = Path(
            ...,
            description='The name of the survey',
        ),
    ):
    """Fetch the results of the given survey."""
    survey = await survey_manager.get(admin, survey)
    return await survey.aggregate()
