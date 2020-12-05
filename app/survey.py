import secrets
import os
import asyncio
import pymongo

from fastapi import HTTPException
from starlette.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError
from cachetools import LRUCache

from app.validation import SubmissionValidator, ConfigurationValidator
from app.aggregation import Alligator
from app.utils import identify, now


# frontend url
FRONTEND_URL = os.getenv('FRONTEND_URL')


class SurveyManager:
    """The manager manages creating, updating and deleting surveys."""

    def __init__(self, database, letterbox):
        """Initialize a survey manager instance."""
        self.database = database
        self.letterbox = letterbox
        self.cache = LRUCache(maxsize=256)
        self.validator = ConfigurationValidator.create()

        loop = asyncio.get_event_loop()

        loop.run_until_complete(self.database['configurations'].create_index(
            keys=[
                ('admin_id', pymongo.ASCENDING),
                ('survey_name', pymongo.ASCENDING)
            ],
            name='admin_id_survey_name_index',
            unique=True,
        ))

    async def fetch(self, admin_name, survey_name):
        """Return the survey object corresponding to admin and survey name."""

        account_data = self.database['accounts'].find_one(
            filter={'admin_name': admin_name},
            projection={'_id': True},
        )
        admin_id = account_data['_id']


        assert set(account_data.keys()) == {'_id'}  # only return admin_id


        survey_id = f'{admin_id}.{survey_name}'
        if survey_id not in self.cache:
            configuration = await self.database['configurations'].find_one(
                filter={'admin_id': admin_id, 'survey_name': survey_name},
                projection={'_id': False, 'admin_id': False},
            )
            if configuration is None:
                raise HTTPException(404, 'survey not found')
            self.cache[survey_id] = Survey(
                configuration,
                self.database,
                self.letterbox,
            )
        return self.cache[survey_id]

    async def create(self, admin_name, survey_name, configuration):
        """Create a new survey configuration in the database and cache."""
        if admin_name != configuration['admin_name']:
            raise HTTPException(400, 'route/configuration admin names differ')
        if survey_name != configuration['survey_name']:
            raise HTTPException(400, 'route/configuration survey names differ')
        if not self.validator.validate(configuration):
            raise HTTPException(400, 'invalid configuration')
        try:
            await self.database['configurations'].insert_one({
                '_id': identify(configuration),
                **configuration,
            })
        except DuplicateKeyError:
            raise HTTPException(400, 'survey exists')
        self.cache[identify(configuration)] = configuration

    async def update(self, admin_name, survey_name, configuration):
        """Update a survey configuration in the database and cache."""
        if admin_name != configuration['admin_name']:
            raise HTTPException(400, 'route/configuration admin names differ')
        if survey_name != configuration['survey_name']:
            raise HTTPException(400, 'route/configuration survey names differ')
        if not self.validator.validate(configuration):
            raise HTTPException(400, 'invalid configuration')

        # TODO should work without specifying _id extra, does it?
        # configuration['_id'] = identify(configuration)

        result = await self.database['configurations'].replace_one(
            # filter={'_id': configuration['_id']},
            filter={'_id': identify(configuration)},
            replacement=configuration,
        )
        if result.matched_count == 0:
            raise HTTPException(400, 'not an existing survey')
        # del configuration['_id']
        self.cache[identify(configuration)] = configuration

    async def sweep(self, admin_name, survey_name):
        """Delete all the submission data of the survey from the database.

        We intentionally do not use self.fetch() here, as we want to delete
        the survey entry in self.delete() before calling self.sweep()

        """
        survey_id = f'{admin_name}.{survey_name}'
        await self.database[f'surveys.{survey_id}.submissions'].drop()
        await self.database[f'surveys.{survey_id}.verified-submissions'].drop()

    async def reset(self, admin_name, survey_name):
        """Delete all submission data including the results of a survey."""
        survey_id = f'{admin_name}.{survey_name}'
        await self.database['results'].delete_one({'_id': survey_id})
        await self.sweep(admin_name, survey_name)

    async def delete(self, admin_name, survey_name):
        """Delete the survey and all its data from the database and cache."""
        survey_id = f'{admin_name}.{survey_name}'
        await self.database['configurations'].delete_one({'_id': survey_id})
        if survey_id in self.cache:
            del self.cache[survey_id]
        await self.reset(admin_name, survey_name)


class Survey:
    """The survey class that all surveys instantiate."""

    def __init__(
            self,
            configuration,
            database,
            letterbox,
    ):
        """Create a survey from the given json configuration file."""
        self.configuration = configuration
        self.admin_name = self.configuration['admin_name']
        self.survey_name = self.configuration['survey_name']
        self.survey_id = identify(configuration)
        self.title = self.configuration['title']
        self.start = self.configuration['start']
        self.end = self.configuration['end']
        self.authentication = self.configuration['authentication']
        self.ei = Survey._get_email_field_index(self.configuration)
        self.validator = SubmissionValidator.create(self.configuration)
        self.letterbox = letterbox
        self.alligator = Alligator(self.configuration, database)
        self.submissions = database[f'surveys.{self.survey_id}.submissions']
        self.vss = database[f'surveys.{self.survey_id}.verified-submissions']
        self.results = None

    @staticmethod
    def _get_email_field_index(configuration):
        """Find the index of the email field in a survey configuration."""
        for index, field in enumerate(configuration['fields']):
            if field['type'] == 'email':
                return index
        return None

    async def submit(self, submission):
        """Save a user submission in the submissions collection."""
        submission_time = now()
        if submission_time < self.start:
            raise HTTPException(400, 'survey is not open yet')
        if submission_time >= self.end:
            raise HTTPException(400, 'survey is closed')
        if not self.validator.validate(submission):
            raise HTTPException(400, 'invalid submission')
        submission = {
            'submission_time': submission_time,
            'data': submission,
        }
        if self.authentication == 'open':
            await self.submissions.insert_one(submission)
        if self.authentication == 'email':
            submission['_id'] = secrets.token_hex(32)
            while True:
                try:
                    await self.submissions.insert_one(submission)
                    break
                except DuplicateKeyError:
                    submission['_id'] = secrets.token_hex(32)
            status = await self.letterbox.send_submission_verification_email(
                self.admin_name,
                self.survey_name,
                self.title,
                submission['data'][str(self.ei + 1)],
                submission['_id'],
            )
            if status != 200:
                raise HTTPException(500, 'email delivery failure')
        if self.authentication == 'invitation':
            raise HTTPException(501, 'not implemented')

    async def verify(self, token):
        """Verify the user's email address and save submission as verified."""
        verification_time = now()
        if self.authentication != 'email':
            raise HTTPException(400, 'survey does not verify email addresses')
        if verification_time < self.start:
            raise HTTPException(400, 'survey is not open yet')
        if verification_time >= self.end:
            raise HTTPException(400, 'survey is closed')
        submission = await self.submissions.find_one({'_id': token})
        if submission is None:
            raise HTTPException(401, 'invalid token')
        submission['verification_time'] = verification_time
        submission['_id'] = submission['data'][str(self.ei + 1)]
        await self.vss.find_one_and_replace(
            filter={'_id': submission['_id']},
            replacement=submission,
            upsert=True,
        )
        return RedirectResponse(
            f'{FRONTEND_URL}/{self.admin_name}/{self.survey_name}/success'
        )

    async def aggregate(self):
        """Query the survey submissions and return aggregated results."""
        if now() < self.end:
            raise HTTPException(400, 'survey is not yet closed')
        self.results = self.results or await self.alligator.fetch()
        return self.results
