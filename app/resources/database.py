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
            keys='username',
            name='username_index',
            unique=True,
        ),
        pymongo.IndexModel(
            keys='email_address',
            name='email_address_index',
            unique=True,
        ),
        pymongo.IndexModel(
            keys='verification_token_hash',
            name='verification_token_hash_index',
            unique=True,
        ),
        pymongo.IndexModel(
            keys='creation_time',
            name='creation_time_index',
            expireAfterSeconds=24*60*60,  # 24 hours
            partialFilterExpression={'verified': {'$eq': False}},
        ),
    ]
)
database['access_tokens'].create_indexes([
        pymongo.IndexModel(
            keys='access_token_hash',
            name='access_token_hash_index',
            unique=True,
        ),
        pymongo.IndexModel(
            keys='issuance_time',
            name='issuance_time_index',
            expireAfterSeconds=14*24*60*60,  # 14 days
        ),
    ]
)
# connect to mongodb via motor
client = motor.motor_asyncio.AsyncIOMotorClient(
    settings.MONGODB_CONNECTION_STRING,
)
# get link to development / production / testing database via motor
database = client[settings.ENVIRONMENT]
