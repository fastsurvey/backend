import os


# check that required environment variables are set
envs = [
    'ENVIRONMENT',
    'FRONTEND_URL',
    'BACKEND_URL',
    'PUBLIC_RSA_KEY',
    'PRIVATE_RSA_KEY',
    'MONGODB_CONNECTION_STRING',
    'MAILGUN_API_KEY',
]
for env in envs:
    assert os.getenv(env), f'environment variable {env} not set'


from fastapi import FastAPI, Path, Query, Body, Form, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient, ASCENDING
from pydantic import BaseModel

from app.mailing import Letterbox
from app.account import AccountManager
from app.survey import SurveyManager
from app.cryptography import JWTManager


# development / production / testing environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
# MongoDB connection string
MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')


# connect to mongodb via pymongo
client = MongoClient(MONGODB_CONNECTION_STRING)
# get link to development / production / testing database via pymongo
database = client[ENVIRONMENT]
# set up database indices synchronously via pymongo
database['configurations'].create_index(
    keys=[('username', ASCENDING), ('survey_name', ASCENDING)],
    name='username_survey_name_index',
    unique=True,
)
database['accounts'].create_index(
    keys='email_address',
    name='email_address_index',
    unique=True,
)
database['accounts'].create_index(
    keys='verification_token',
    name='verification_token_index',
    unique=True,
)
database['accounts'].create_index(
    keys='creation_time',
    name='creation_time_index',
    expireAfterSeconds=10*60,  # delete draft accounts after 10 mins
    partialFilterExpression={'verified': {'$eq': False}},
)


# create fastapi app
app = FastAPI()
# connect to mongodb via motor
client = AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
# get link to development / production / testing database via motor
database = client[ENVIRONMENT]
# create email client
letterbox = Letterbox()
# create JWT manager
jwt_manager = JWTManager()
# instantiate survey manager
survey_manager = SurveyManager(database, letterbox, jwt_manager)
# instantiate account manager
account_manager = AccountManager(
    database,
    letterbox,
    jwt_manager,
    survey_manager,
)
# fastapi password bearer
oauth2_scheme = OAuth2PasswordBearer('/authentication')


class ExceptionResponse(BaseModel):
    detail: str


configuration_example = {
    'survey_name': 'option',
    'title': 'Option Test',
    'description': '',
    'start': 1000000000,
    'end': 2000000000,
    'draft': False,
    'authentication': 'open',
    'limit': 0,
    'fields': [
        {
            'type': 'option',
            'title': 'I have read and agree to the terms and conditions',
            'description': '',
            'required': True
        }
    ],
}
submission_example = {
    '1': True,
}


PAR_USERNAME = Path(
    ...,
    description='The name of the user',
    example='fastsurvey',
)
PAR_EMAIL = Form(
    ...,
    description='The users\'s email address',
    example='support@fastsurvey.io',
)
PAR_PASSWORD = Form(
    ...,
    description='The account password',
    example='12345678',
)
PAR_SURVEY_NAME = Path(
    ...,
    description='The name of the survey',
    example='hello-world',
)
PAR_CONFIGURATION = Body(
    ...,
    description='The new configuration',
    example=configuration_example
)


@app.get(
    path='/users/{username}',
    responses={
        200: {
            'content': {
                'application/json': {
                    'example': {
                        'username': 'fastsurvey',
                        'email_address': 'support@fastsurvey.io',
                        'verified': True,
                    },
                },
            },
        },
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid access token',
                    },
                },
            },
        },
        404: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'account not found',
                    },
                },
            },
        },
    },
)
async def fetch_user(
        username: str = PAR_USERNAME,
        access_token: str = Depends(oauth2_scheme),
    ):
    """Fetch the given user's account data."""
    return await account_manager.fetch(username, access_token)


@app.post(
    path='/users/{username}',
    responses={
        400: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'examples': {
                        'invalid account data': {
                            'value': {
                                'detail': 'invalid account data',
                            },
                        },
                        'username already taken': {
                            'value': {
                                'detail': 'username already taken',
                            },
                        },
                        'email address already taken': {
                            'value': {
                                'detail': 'email address already taken',
                            },
                        },
                    },
                },
            },
        },
    },
)
async def create_user(
        username: str = PAR_USERNAME,
        email: str = PAR_EMAIL,
        password: str = PAR_PASSWORD,
    ):
    """Create a new user with default account data."""
    await account_manager.create(username, email, password)


@app.put(
    path='/users/{username}',
    responses={
        400: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid account data',
                    },
                },
            },
        },
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid access token',
                    },
                },
            },
        },
        404: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'account not found',
                    },
                },
            },
        },
    },
)
async def update_user(
        username: str = PAR_USERNAME,
        account_data: dict = Body(
            ...,
            description='The updated account data',
            example={
                'username': 'fastsurvey',
                'email_address': 'support@fastsurvey.io',
            },
        ),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Update the given user's account data."""
    await account_manager.update(username, account_data, access_token)


@app.delete(
    path='/users/{username}',
    responses={
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid access token',
                    },
                },
            },
        },
    },
)
async def delete_user(
        username: str = PAR_USERNAME,
        access_token: str = Depends(oauth2_scheme),
    ):
    """Delete the user and all her surveys from the database."""
    await account_manager.delete(username, access_token)


@app.get(
    path='/users/{username}/surveys',
    responses={
        200: {
            'content': {
                'application/json': {
                    'example': [configuration_example],
                },
            },
        },
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid access token',
                    },
                },
            },
        },
    },
)
async def fetch_surveys(
        username: str = PAR_USERNAME,
        skip: int = Query(
            0,
            description='The index of the first returned configuration',
            example=0,
        ),
        limit: int = Query(
            10,
            description='The query result count limit; 0 means no limit',
            example=10,
        ),
        access_token: str = Depends(oauth2_scheme),
    ):
    """Fetch the user's survey configurations sorted by the start date."""
    return await account_manager.fetch_configurations(
        username,
        skip,
        limit,
        access_token,
    )


@app.get(
    path='/users/{username}/surveys/{survey_name}',
    responses={
        200: {
            'content': {
                'application/json': {
                    'example': configuration_example,
                },
            },
        },
        404: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'survey not found',
                    },
                },
            },
        },
    },
)
async def fetch_survey(
        username: str = PAR_USERNAME,
        survey_name: str = PAR_SURVEY_NAME,
    ):
    """Fetch a survey configuration."""
    return await survey_manager.fetch(username, survey_name)


@app.post(
    path='/users/{username}/surveys/{survey_name}',
    responses={
        400: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'examples': {
                        'invalid configuration': {
                            'value': {
                                'detail': 'invalid configuration',
                            },
                        },
                        'survey exists': {
                            'value': {
                                'detail': 'survey exists',
                            },
                        },
                    },
                },
            },
        },
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid access token',
                    },
                },
            },
        },
    },
)
async def create_survey(
        username: str = PAR_USERNAME,
        survey_name: str = PAR_SURVEY_NAME,
        configuration: dict = PAR_CONFIGURATION,
        access_token: str = Depends(oauth2_scheme),
    ):
    """Create new survey with given configuration."""
    await survey_manager.create(
        username,
        survey_name,
        configuration,
        access_token,
    )


@app.put(
    path='/users/{username}/surveys/{survey_name}',
    responses={
        400: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'examples': {
                        'invalid configuration': {
                            'value': {
                                'detail': 'invalid configuration',
                            },
                        },
                        'survey exists': {
                            'value': {
                                'detail': 'not an existing survey',
                            },
                        },
                    },
                },
            },
        },
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid access token',
                    },
                },
            },
        },
    },
)
async def update_survey(
        username: str = PAR_USERNAME,
        survey_name: str = PAR_SURVEY_NAME,
        configuration: dict = PAR_CONFIGURATION,
        access_token: str = Depends(oauth2_scheme),
    ):
    """Update survey with given configuration."""
    await survey_manager.update(
        username,
        survey_name,
        configuration,
        access_token,
    )


@app.delete(
    path='/users/{username}/surveys/{survey_name}',
    responses={
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid access token',
                    },
                },
            },
        },
    },
)
async def delete_survey(
        username: str = PAR_USERNAME,
        survey_name: str = PAR_SURVEY_NAME,
        access_token: str = Depends(oauth2_scheme),
    ):
    """Delete given survey including all its submissions and other data."""
    await survey_manager.delete(username, survey_name, access_token)


@app.post(
    path='/users/{username}/surveys/{survey_name}/submissions',
    responses={
        400: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'examples': {
                        'survey is not open yet': {
                            'value': {
                                'detail': 'survey is not open yet',
                            },
                        },
                        'survey is closed': {
                            'value': {
                                'detail': 'survey is closed',
                            },
                        },
                        'invalid submission': {
                            'value': {
                                'detail': 'invalid submission',
                            },
                        },
                    },
                },
            },
        },
        404: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'survey not found',
                    },
                },
            },
        },
    },
)
async def create_submission(
        username: str = PAR_USERNAME,
        survey_name: str = PAR_SURVEY_NAME,
        submission: dict = Body(
            ...,
            description='The user submission',
            example=submission_example,
        ),
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager._fetch(username, survey_name)
    return await survey.submit(submission)


@app.delete(
    path='/users/{username}/surveys/{survey_name}/submissions',
    responses={
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid access token',
                    },
                },
            },
        },
    },
)
async def reset_survey(
        username: str = PAR_USERNAME,
        survey_name: str = PAR_SURVEY_NAME,
        access_token: str = Depends(oauth2_scheme),
    ):
    """Reset a survey by deleting all submission data including any results."""
    await survey_manager.reset(username, survey_name, access_token)


@app.get(
    path='/users/{username}/surveys/{survey_name}/verification/{token}',
    responses={
        400: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'examples': {
                        'invalid token': {
                            'value': {
                                'detail': 'survey does not verify email addresses',
                            },
                        },
                        'survey is not open yet': {
                            'value': {
                                'detail': 'survey is not open yet',
                            },
                        },
                        'survey is closed': {
                            'value': {
                                'detail': 'survey is closed',
                            },
                        },
                    },
                },
            },
        },
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid verification token',
                    },
                },
            },
        },
        404: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'survey not found',
                    },
                },
            },
        },
    },
)
async def verify_submission(
        username: str = PAR_USERNAME,
        survey_name: str = PAR_SURVEY_NAME,
        token: str = Path(..., description='The verification token'),
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager._fetch(username, survey_name)
    return await survey.verify(token)


@app.get(
    path='/users/{username}/surveys/{survey_name}/results',
    responses={
        200: {
            'content': {
                'application/json': {
                    'example': {
                        'count': 1,
                        '1': 1,
                    },
                },
            },
        },
        400: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'survey is not yet closed',
                    },
                },
            },
        },
        404: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'survey not found',
                    },
                },
            },
        },
    },
)
async def fetch_results(
        username: str = PAR_USERNAME,
        survey_name: str = PAR_SURVEY_NAME,
    ):
    """Fetch the results of the given survey."""

    # TODO adapt result following authentication

    survey = await survey_manager._fetch(username, survey_name)
    return await survey.aggregate()


@app.post(
    path='/authentication',
    responses={
        200: {
            'content': {
                'application/json': {
                    'example': {
                        'access_token': b'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJGYXN0U3VydmV5Iiwic3ViIjoiYXBwbGUiLCJpYXQiOjE2MTYzNTA5NjAsImV4cCI6MTYxNjM1ODE2MH0.Vl8ndfMgE-LKcH5GOZZ_JEn2rL87Mg9wpihTvo-Cfukqr3vBI6I49EP109B2ZnEASnoXSzDRQSM438Pxxpm6aFMGSaxCJvVbPN3YhxKDKWel-3t7cslF5iwE8AlsYHQV6_6JZv-bZolUmScnGjXKEUBWn3x72AeFBm5I4O4VRWDt96umGfgtaPkBvXwW0eDIbGDIXR-MQF0vjiGnEd0GYwexgCj0uO80QTlN2oIH1kFtb612oqWJ3_Ipb2Ui6jwo0wVZW_I7zi5rKGrELsdGManwt7wUgp-V4779XXZ33IuojgS6kO45-aAkppBycv3cDqQdR_yjoRy6sZ4nryHEPzYKPtumtuY28Va2d9RpSxVHo1DkiyXmlrVWnmzyOuFVUxAMmblwaslc0es4igWtX_bZ141Vb6Vj96xk6pR6Wq9jjEhw9RsfyIVr2TwplzZZayVDl_9Pou3b8cZGRlotAYgWlYj9h0ZiI7hUvvXD24sFykx_HV3-hBPJJDmW3jwPRvRUtZEMic-1jAy-gMJs-irmeVOW6_Mh8LLncTRfutwJI4k6TqnPguX3LKEWu3uyGKT5zT2ZXanaTmBRVuFbON7-xb6ZvncdI5ttALixff2O67gXUjM7E9OrbauVWN6xqQ4-Wv70VJvtJa1MEvZOtC-JGwaF6C2WFNYKbnvB6hY',
                        'token_type': 'bearer',
                    },
                },
            },
        },
        400: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'account not verified',
                    },
                },
            },
        },
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'invalid password',
                    },
                },
            },
        },
        404: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'account not found',
                    },
                },
            },
        },
    },
)
async def authenticate_user(
        identifier: str = Form(
            ...,
            description='The email address or username',
            example='fastsurvey',
        ),
        password: str = PAR_PASSWORD,
    ):
    return await account_manager.authenticate(identifier, password)


@app.post(
    path='/verification',
    responses={
        200: {
            'content': {
                'application/json': {
                    'example': {
                        'access_token': b'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJGYXN0U3VydmV5Iiwic3ViIjoiYXBwbGUiLCJpYXQiOjE2MTYzNTA5NjAsImV4cCI6MTYxNjM1ODE2MH0.Vl8ndfMgE-LKcH5GOZZ_JEn2rL87Mg9wpihTvo-Cfukqr3vBI6I49EP109B2ZnEASnoXSzDRQSM438Pxxpm6aFMGSaxCJvVbPN3YhxKDKWel-3t7cslF5iwE8AlsYHQV6_6JZv-bZolUmScnGjXKEUBWn3x72AeFBm5I4O4VRWDt96umGfgtaPkBvXwW0eDIbGDIXR-MQF0vjiGnEd0GYwexgCj0uO80QTlN2oIH1kFtb612oqWJ3_Ipb2Ui6jwo0wVZW_I7zi5rKGrELsdGManwt7wUgp-V4779XXZ33IuojgS6kO45-aAkppBycv3cDqQdR_yjoRy6sZ4nryHEPzYKPtumtuY28Va2d9RpSxVHo1DkiyXmlrVWnmzyOuFVUxAMmblwaslc0es4igWtX_bZ141Vb6Vj96xk6pR6Wq9jjEhw9RsfyIVr2TwplzZZayVDl_9Pou3b8cZGRlotAYgWlYj9h0ZiI7hUvvXD24sFykx_HV3-hBPJJDmW3jwPRvRUtZEMic-1jAy-gMJs-irmeVOW6_Mh8LLncTRfutwJI4k6TqnPguX3LKEWu3uyGKT5zT2ZXanaTmBRVuFbON7-xb6ZvncdI5ttALixff2O67gXUjM7E9OrbauVWN6xqQ4-Wv70VJvtJa1MEvZOtC-JGwaF6C2WFNYKbnvB6hY',
                        'token_type': 'bearer',
                    },
                },
            },
        },
        400: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'example': {
                        'detail': 'account already verified',
                    },
                },
            },
        },
        401: {
            'model': ExceptionResponse,
            'content': {
                'application/json': {
                    'examples': {
                        'invalid token': {
                            'value': {
                                'detail': 'invalid verification token',
                            },
                        },
                        'invalid password': {
                            'value': {
                                'detail': 'invalid password',
                            },
                        },
                    },
                },
            },
        },
    },
)
async def verify_email_address(
        token: str = Form(..., description='The account verification token'),
        password: str = PAR_PASSWORD,
    ):
    return await account_manager.verify(token, password)
