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
subdomain = dict(test='test.', development='dev.', production='')[ENVIRONMENT]

# frontend url
FRONTEND_URL = f'https://{subdomain}fastsurvey.de'
# console url
CONSOLE_URL = f'https://console.{subdomain}fastsurvey.de'
# backend url
BACKEND_URL = f'https://api.{subdomain}fastsurvey.de'
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
