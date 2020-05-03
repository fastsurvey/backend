

from flask import Flask
from flask_cors import CORS

import os
import certifi
from pymongo import MongoClient
from google.cloud import datastore


# Set correct SSL certificate
os.environ['SSL_CERT_FILE'] = certifi.where()



if None in [os.getenv("MONGODB_WRITE_CONNECTION_STRING"), os.getenv("SENDGRID_API_KEY"), os.getenv("BACKEND_URL")]:
    # If any of the required environment variables has not been set the we take them from secrets.py
    print("LOCAL SECRETS")
    from flask_backend.secrets import MONGODB_WRITE_CONNECTION_STRING, SENDGRID_API_KEY, BACKEND_URL
else:
    print("DATASTORE SECRETS")
    MONGODB_WRITE_CONNECTION_STRING = os.getenv('MONGODB_WRITE_CONNECTION_STRING')
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    BACKEND_URL = os.getenv('BACKEND_URL')


# haven't configured datastore yet
"""
# We need this to access our environment variables in the gcloud datastore
if os.getenv("ENVIRONMENT") != "production":
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"

client = datastore.Client()
raw_query_result = list(client.query(kind='Secrets').fetch())
for entity in raw_query_result:
    os.environ[entity["name"]] = entity["value"]

MONGODB_WRITE_CONNECTION_STRING = os.getenv('MONGODB_WRITE_CONNECTION_STRING')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
BACKEND_URL = os.getenv('BACKEND_URL')
FRONTEND_URL = os.getenv('FRONTEND_URL')
"""

if os.getenv("ENVIRONMENT") != "production":
    from flask_backend.secrets import MONGODB_WRITE_CONNECTION_STRING, SENDGRID_API_KEY, BACKEND_URL, FRONTEND_URL


# Connect to database and collections
client = MongoClient(MONGODB_WRITE_CONNECTION_STRING)

survey_1_database = client.get_database('survey_1_database')
survey_1_verified_entries = survey_1_database['verified_entries']
survey_1_pending_entries = survey_1_database['pending_entries']



app = Flask(__name__)

# Cookies (only form data) are stored for 1 day
app.config['REMEMBER_COOKIE_DURATION'] = 60 * 60 * 24 * 1

cors = CORS(app)



from flask_backend import routes
