import os
import json

from fastapi import FastAPI, Path, Body
from enum import Enum 
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

import credentials
import survey


MDBCSTR = credentials.MDB_CONNECTION_STRING


# create fastapi app
app = FastAPI()

# connect to mongodb via pymongo and motor
mongo_client = MongoClient(MDBCSTR)
motor_client = AsyncIOMotorClient(MDBCSTR)


def create_surveys():
    """Read survey configuration files and translate them to survey objects."""
    surveys = []
    cns = mongo_client['main']['configurations']
    for cn in cns.find(projection={'_id': False}):
        surveys.append(
            survey.Survey(
                configuration=cn,
                database=motor_client['main'],
            )
        )
    return {sv.name: sv for sv in surveys}


# create survey objects from configuration files
surveys = create_surveys()
SurveyName = Enum('SurveyName', {k: k for k in surveys.keys()}, type=str)


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


@app.post('/{survey}/submit', tags=['survey'])
async def submit(
        survey: SurveyName = Path(
            ...,
            description='The identification tag of the survey',
        ),
        submission: dict = Body(
            ...,
            description='The user submission for the survey',
        )
    ):
    """Validate submission and store it under pending submissions"""
    return await surveys[survey].submit(submission)


@app.get('/{survey}/verify/{token}', tags=['survey'])
async def verify(
        survey: SurveyName = Path(
            ...,
            description='The identification tag of the survey',
        ),
        token: str = Path(
            ...,
            description='The verification token',
        ),
    ):
    """Verify user token and either fail or redirect to success page"""
    return await surveys[survey].verify(token)


@app.get('/{survey}/results', tags=['survey'])
async def results(
        survey: SurveyName = Path(
            ...,
            description='The identification tag of the survey',
        ),
    ):
    """Fetch the results of the given survey"""
    return await surveys[survey].fetch()
