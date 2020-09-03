import os
import json

from fastapi import FastAPI, Path, Body, HTTPException
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient

from app.credentials import MDB_CONNECTION_STRING
from app.survey import SurveyManager


MDBCSTR = MDB_CONNECTION_STRING


# create fastapi app
app = FastAPI()
# connect to mongodb via pymongo and motor
motor_client = AsyncIOMotorClient(MDBCSTR)
# get link to database
database = motor_client['main']
# instantiate survey manager
manager = SurveyManager(database)


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
