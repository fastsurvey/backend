import os

from fastapi import FastAPI, Path
from enum import Enum 
from starlette.responses import RedirectResponse


FURL = os.getenv('FRONTEND_URL')  # frontend url
BURL = os.getenv('BACKEND_URL')  # backend url


# create fastapi app
app = FastAPI()


class SurveyName(str, Enum):
    s1 = '20200504'
    s2 = 'fvv-ss20-referate'
    s3 = 'fvv-ss20-go'
    s4 = 'fvv-ss20-leitung'


@app.get('/')
async def status():
    """Verify if database and mailing service are operational"""
    try:
        # TODO test if services are operational
        return {'status': 'all services operational'}
    except:
        return {'status': 'database error'}


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
