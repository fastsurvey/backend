import os

from fastapi import FastAPI, Path, Body, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.mailing import Letterbox
from app.survey import SurveyManager


# dev / production environment
ENV = os.getenv('ENV')
# MongoDB connection string
MDBCS = os.getenv('MDBCS')
# Postmark dev / production server token
# PMST = os.getenv('DPMST' if ENV == 'development' else 'PPMST')


# create fastapi app
app = FastAPI()
# connect to mongodb via pymongo and motor
motor_client = AsyncIOMotorClient(MDBCS)
# get link to dev / production database
database = motor_client[ENV]
# create email client
letterbox = Letterbox()
# instantiate survey manager
survey_manager = SurveyManager(database, letterbox)


@app.get('/status', tags=['status'])
async def status():
    """Verify if database and mailing services are operational."""
    status = {'database': 'UP', 'mailing': 'UP'}
    try:
        await motor_client.server_info()
    except:
        status['database'] = 'DOWN'
    '''
    try:
        status['mailing'] = email_client.status.get()['status']
    except:
        status['mailing'] = 'DOWN'
    '''
    return status


@app.get('/{admin_name}/{survey_name}', tags=['survey'])
async def fetch(
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


@app.post('/{admin_name}/{survey_name}/submission', tags=['sujvey'])
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


@app.get('/{admin_name}/{survey_name}/verification/{token}', tags=['survey'])
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


@app.get('/{admin_name}/{survey_name}/results', tags=['survey'])
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
