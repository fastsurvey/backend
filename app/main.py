import os
import json

from fastapi import FastAPI, Path, Body, HTTPException
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
    """Fetch survey configurations and translate them to survey objects."""
    configurations = mongo_client['main']['configurations']
    surveys = {
        cn['_id']: survey.Survey(
            configuration=cn,
            database=motor_client['main'],
        )
        for cn
        in configurations.find()
    }
    return surveys


# create survey objects from configurations
surveys = create_surveys()


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
    identifier = f'{admin}.{survey}'
    if identifier not in surveys:
        raise HTTPException(404, 'survey not found')
    return await surveys[identifier].submit(submission)


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
    identifier = f'{admin}.{survey}'
    if identifier not in surveys:
        raise HTTPException(404, 'survey not found')
    return await surveys[identifier].verify(token)


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
    identifier = f'{admin}.{survey}'
    if identifier not in surveys:
        raise HTTPException(404, 'survey not found')
    return await surveys[identifier].fetch()
