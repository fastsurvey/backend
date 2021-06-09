import pymongo
import motor.motor_asyncio

import app.settings as settings


# connect to mongodb via pymongo
client = pymongo.MongoClient(settings.MONGODB_CONNECTION_STRING)
# get link to development / production / testing database via pymongo
database = client[settings.ENVIRONMENT]
# set up database indices synchronously via pymongo
database['configurations'].create_index(
    keys=[('username', pymongo.ASCENDING), ('survey_name', pymongo.ASCENDING)],
    name='username_survey_name_index',
    unique=True,
)
database['accounts'].create_indexes([
        pymongo.IndexModel(
            keys='email_address',
            name='email_address_index',
            unique=True,
        ),
        pymongo.IndexModel(
            keys='verification_token',
            name='verification_token_index',
            unique=True,
        ),
        pymongo.IndexModel(
            keys='creation_time',
            name='creation_time_index',
            expireAfterSeconds=24*60*60,  # delete draft accounts after 24 hours
            partialFilterExpression={'verified': {'$eq': False}},
        ),
    ]
)
# connect to mongodb via motor
client = motor.motor_asyncio.AsyncIOMotorClient(
    settings.MONGODB_CONNECTION_STRING,
)
# get link to development / production / testing database via motor
database = client[settings.ENVIRONMENT]
