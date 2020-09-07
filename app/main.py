import os
import json

from fastapi import FastAPI, Path, Body, HTTPException
from enum import Enum
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
manager = SurveyManager(database, postmark)


@app.get('/', tags=['status'])
async def status():
    """Verify if database and mailing services are operational"""
    try:
        await motor_client.server_info()
        # TODO add test for sending emails
    except:
        return {'status': 'database error'}
    else:
        return {'status': 'all services operational'}


@app.get('/{admin}/{survey}', tags=['survey'])
async def configure(
        admin: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey: str = Path(
            ...,
            description='The name of the survey',
        ),
    ):
    """Fetch the configuration document of the given survey"""
    survey = await manager.get(admin, survey)
    return survey.cn


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
    """Validate submission and store it under pending submissions"""
    survey = await manager.get(admin, survey)
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
    """Verify user token and either fail or redirect to success page"""
    survey = await manager.get(admin, survey)
    return await survey.verify(token)


@app.get('/{admin}/{survey}/results', tags=['survey'])
async def results(
        admin: str = Path(
            ...,
            description='The name of the admin',
        ),
        survey: str = Path(
            ...,
            description='The name of the survey',
        ),
    ):
    """Fetch the results of the given survey"""
    survey = await manager.get(admin, survey)
    return await survey.fetch()
