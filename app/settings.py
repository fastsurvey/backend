import os

import app.utils as utils


# check that required environment variables are set
_VARS = [
    "ENVIRONMENT",
    "MONGODB_CONNECTION_STRING",
    "POSTMARK_SERVER_TOKEN",
    "COMMIT_SHA",
    "BRANCH_NAME",
]
for var in _VARS:
    assert os.getenv(var), f"environment variable {var} not set"

# test / development / production environment
ENVIRONMENT = os.getenv("ENVIRONMENT")
assert ENVIRONMENT in ["test", "development", "production"]
subdomain = {"test": "test.", "development": "dev."}.get(ENVIRONMENT, "")

# frontend url
FRONTEND_URL = f"https://{subdomain}fastsurvey.de"
# console url
CONSOLE_URL = f"https://console.{subdomain}fastsurvey.de"
# MongoDB connection string
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
# Postmark server token
POSTMARK_SERVER_TOKEN = os.getenv("POSTMARK_SERVER_TOKEN")
# sender email address
SENDER = "FastSurvey <support@fastsurvey.de>"
# git commit hash
COMMIT_SHA = os.getenv("COMMIT_SHA")
# git branch name
BRANCH_NAME = os.getenv("BRANCH_NAME")
# timestamp of when the server was started
START_TIME = utils.timestamp()
