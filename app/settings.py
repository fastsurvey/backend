import os

import app.utils as utils


# check that required environment variables are set
_VARS = [
    'ENVIRONMENT',
    'MONGODB_CONNECTION_STRING',
    'MAILGUN_API_KEY',
    'COMMIT_SHA',
    'BRANCH_NAME',
]
for var in _VARS:
    assert os.getenv(var), f'environment variable {var} not set'


# test / development / production environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
assert ENVIRONMENT in ['test', 'development', 'production']
# frontend url
_URLS = {
    'production': 'fastsurvey.de',
    'development': 'dev.fastsurvey.de',
    'test': 'test.fastsurvey.de',
}
FRONTEND_URL = _URLS[ENVIRONMENT]
# console url
CONSOLE_URL = f'console.{FRONTEND_URL}'
# backend url
BACKEND_URL = f'api.{FRONTEND_URL}'
# MongoDB connection string
MONGODB_CONNECTION_STRING = os.getenv('MONGODB_CONNECTION_STRING')
# Mailgun api key
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
# Mailgun email endpoint
MAILGUN_ENDPOINT = 'https://api.eu.mailgun.net/v3/email.fastsurvey.de'
# sender email address
SENDER = 'FastSurvey <noreply@fastsurvey.de>'
# git commit hash
COMMIT_SHA = os.getenv('COMMIT_SHA')
# git branch name
BRANCH_NAME = os.getenv('BRANCH_NAME')
# timestamp of when the server was started
START_TIME = utils.now()
