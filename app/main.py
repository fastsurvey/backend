import os

from fastapi import FastAPI, Path
from enum import Enum 
from starlette.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient

from . import credentials


MDBCSTR = credentials.MDB_CONNECTION_STRING
FURL = credentials.FRONTEND_URL
BURL = credentials.BACKEND_URL


# create fastapi app
app = FastAPI()

# connect to mongodb via motor
client = AsyncIOMotorClient(MDBCSTR)
db = client['survey_database']


class SurveyName(str, Enum):
    s1 = '20200504'
    s2 = 'fvv-ss20-referate'
    s3 = 'fvv-ss20-go'
    s4 = 'fvv-ss20-leitung'


@app.get('/')
async def status():
    """Verify if database and mailing service are operational"""
    try:
        await client.server_info()
        # TODO add test for sending emails
    except:
        return {'status': 'database error'}
    else:
        return {'status': 'all services operational'}


@app.post('/{survey}/submit')
async def submit(
        survey: SurveyName = Path(
            ...,
            description='The identification tag of the survey',
        ),
    ):
    """Check if requested survey is open and submit choice for verification"""
    # TODO check if survey is open and submit or fail
    pass


@app.get('/{survey}/verify/{token}')
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
    # TODO verify token and redirect or fail
    return RedirectResponse(f'{FURL}/{survey}/success')


@app.get('/{survey}/results')
async def results():
    """Fetch and return the survey results from database"""
    # TODO fetch results
    pass
