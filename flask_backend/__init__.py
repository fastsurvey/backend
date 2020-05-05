

from flask import Flask
from flask_cors import CORS

import os
import certifi
from pymongo import MongoClient
from google.cloud import datastore


# Set correct SSL certificate
os.environ['SSL_CERT_FILE'] = certifi.where()


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
    from admin.secrets import MONGODB_WRITE_CONNECTION_STRING, SENDGRID_API_KEY, BACKEND_URL, FRONTEND_URL
"""

# print(os.environ)

# Connect to database and collections
client = MongoClient(MONGODB_WRITE_CONNECTION_STRING)

survey_database = client.get_database('survey_database')
verified_entries_collection = survey_database['verified_entries']
pending_entries_collection = survey_database['pending_entries']
time_limits_collection = survey_database['time_limits']


app = Flask(__name__)

# Cookies (only form data) are stored for 1 day
app.config['REMEMBER_COOKIE_DURATION'] = 60 * 60 * 24 * 1

cors = CORS(app)



from flask_backend import routes
