

from flask import Flask
from flask_cors import CORS

import os
import certifi
from pymongo import MongoClient



# Set correct SSL certificate
os.environ['SSL_CERT_FILE'] = certifi.where()




if None in [os.getenv("MONGODB_WRITE_CONNECTION_STRING"), os.getenv("SENDGRID_API_KEY"), os.getenv("BACKEND_URL")]:
    from flask_backend.secrets import MONGODB_WRITE_CONNECTION_STRING, SENDGRID_API_KEY, BACKEND_URL
else:
    MONGODB_WRITE_CONNECTION_STRING = os.getenv('MONGODB_WRITE_CONNECTION_STRING')
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    BACKEND_URL = os.getenv('BACKEND_URL')


# Connect to database and collections
client = MongoClient(MONGODB_WRITE_CONNECTION_STRING)

survey_1_database = client.get_database('survey_1_database')
verified_entries_collection = survey_1_database['verified_entries']
pending_entries_collection = survey_1_database['pending_entries']



app = Flask(__name__)

# Cookies (only form data) are stored for 1 day
app.config['REMEMBER_COOKIE_DURATION'] = 60 * 60 * 24 * 1

cors = CORS(app)



from flask_backend import routes
