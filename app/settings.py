import os
import base64

import app.utils as utils


# check that required environment variables are set
_ENVS = [
    'ENVIRONMENT',
    'FRONTEND_URL',
    'CONSOLE_URL',
    'BACKEND_URL',
    'PUBLIC_RSA_KEY',
    'PRIVATE_RSA_KEY',
    'MONGODB_CONNECTION_STRING',
    'MAILGUN_API_KEY',
    'COMMIT_SHA',
    'BRANCH_NAME',
]
for env in _ENVS:
    assert os.getenv(env), f'environment variable {env} not set'


# development / production / test environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
# frontend url
FRONTEND_URL = os.getenv('FRONTEND_URL')
# console url
CONSOLE_URL = os.getenv('CONSOLE_URL')
# backend url
BACKEND_URL = os.getenv('BACKEND_URL')
# public JSON Web Token signature key
PUBLIC_RSA_KEY = base64.b64decode(os.getenv('PUBLIC_RSA_KEY'))
# private JSON Web Token signature key
PRIVATE_RSA_KEY = base64.b64decode(os.getenv('PRIVATE_RSA_KEY'))
# MongoDB connection string
MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')
# Mailgun api key
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
# git commit hash
COMMIT_SHA = os.getenv('COMMIT_SHA')
# git branch name
BRANCH_NAME = os.getenv('BRANCH_NAME')
# timestamp of when the server was started
START_TIME = utils.now()
# sender email address
SENDER = 'FastSurvey <noreply@fastsurvey.io>'
