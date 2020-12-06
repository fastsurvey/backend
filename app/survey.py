import secrets
import os
import asyncio

from fastapi import HTTPException
from starlette.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError
from pymongo import ASCENDING
from cachetools import LRUCache

from app.validation import SubmissionValidator, ConfigurationValidator
from app.aggregation import Alligator
from app.utils import identify, now


# frontend url
FRONTEND_URL = os.getenv('FRONTEND_URL')


class SurveyManager:
    """The manager manages creating, updating and deleting surveys."""

    def __init__(self, database, letterbox, token_manager):
        """Initialize a survey manager instance."""
        self.database = database
        self.letterbox = letterbox
        self.cache = LRUCache(maxsize=256)
        self.validator = ConfigurationValidator.create()
        self.token_manager = token_manager

        loop = asyncio.get_event_loop()

        loop.run_until_complete(self.database['configurations'].create_index(
            keys=[('admin_id', ASCENDING), ('survey_name', ASCENDING)],
            name='admin_id_survey_name_index',
            unique=True,
        ))

    async def _get_admin_id(self, admin_name):
        """Look up the primary admin key from her username."""
        account_data = await self.database['accounts'].find_one(
            filter={'admin_name': admin_name},
            projection={'_id': True},
        )
        if account_data is None:
            raise HTTPException(404, 'admin not found')
        admin_id = account_data['_id']

        assert set(account_data.keys()) == {'_id'}  # only return admin_id

        return admin_id

    async def fetch(self, admin_name, survey_name):
        """Return the survey object corresponding to admin and survey name."""
        admin_id = await self._get_admin_id(admin_name)
        survey_id = identify(admin_id, survey_name)
        if survey_id not in self.cache:
            configuration = await self.database['configurations'].find_one(
                filter={'admin_id': admin_id, 'survey_name': survey_name},
                projection={'_id': False, 'admin_id': False},
            )
            if configuration is None:
                raise HTTPException(404, 'survey not found')
            self.cache[survey_id] = Survey(
                survey_id,
                configuration,
                self.database,
                self.letterbox,
            )
        return self.cache[survey_id]

    async def create(
            self,
            admin_name,
            survey_name,
            configuration,
            access_token,
        ):
        """Create a new survey configuration in the database and cache."""
        admin_id = await self._get_admin_id(admin_name)
        if admin_id != self.token_manager.decode(access_token):
            raise HTTPException(401, 'unauthorized')
        if survey_name != configuration['survey_name']:
            raise HTTPException(400, 'route/configuration survey names differ')
        if not self.validator.validate(configuration):
            raise HTTPException(400, 'invalid configuration')
        try:
            await self.database['configurations'].insert_one({
                'admin_id': admin_id,
                **configuration,
            })
        except DuplicateKeyError:
            raise HTTPException(400, 'survey exists')
        self.cache[identify(admin_id, survey_name)] = configuration

    async def update(
            self,
            admin_name,
            survey_name,
            configuration,
            access_token,
        ):
        """Update a survey configuration in the database and cache."""
        admin_id = await self._get_admin_id(admin_name)
        if admin_id != self.token_manager.decode(access_token):
            raise HTTPException(401, 'unauthorized')
        if survey_name != configuration['survey_name']:
            raise HTTPException(400, 'route/configuration survey names differ')
        if not self.validator.validate(configuration):
            raise HTTPException(400, 'invalid configuration')
        result = await self.database['configurations'].replace_one(
            filter={
                'admin_id': admin_id,
                'survey_name': configuration['survey_name'],
            },
            replacement={'admin_id': admin_id, **configuration}
        )
        if result.matched_count == 0:
            raise HTTPException(400, 'not an existing survey')
        self.cache[identify(admin_id, survey_name)] = configuration

    async def _archive(self, admin_id, survey_name):
        """Delete submission data of a survey, but keep the results."""
        survey_id = identify(admin_id, survey_name)
        await self.database[f'surveys.{survey_id}.submissions'].drop()
        await self.database[f'surveys.{survey_id}.verified-submissions'].drop()

    async def reset(self, admin_name, survey_name, access_token):
        """Delete all submission data including the results of a survey."""
        admin_id = await self._get_admin_id(admin_name)
        if admin_id != self.token_manager.decode(access_token):
            raise HTTPException(401, 'unauthorized')
        survey_id = identify(admin_id, survey_name)
        await self.database['results'].delete_one({'_id': survey_id})
        await self.database[f'surveys.{survey_id}.submissions'].drop()
        await self.database[f'surveys.{survey_id}.verified-submissions'].drop()

    async def delete(self, admin_name, survey_name, access_token):
        """Delete the survey and all its data from the database and cache."""
        admin_id = await self._get_admin_id(admin_name)

        print(admin_id)
        print(self.token_manager.decode(access_token))

        if admin_id != self.token_manager.decode(access_token):
            raise HTTPException(401, 'unauthorized')
        survey_id = identify(admin_id, survey_name)
        await self.database['configurations'].delete_one(
            filter={'admin_id': admin_id, 'survey_name': survey_name},
        )
        if survey_id in self.cache:
            del self.cache[survey_id]
        await self.database['results'].delete_one({'_id': survey_id})
        await self.database[f'surveys.{survey_id}.submissions'].drop()
        await self.database[f'surveys.{survey_id}.verified-submissions'].drop()


class Survey:
    """The survey class that all surveys instantiate."""

    def __init__(
            self,
            survey_id,
            configuration,
            database,
            letterbox,
    ):
        """Create a survey from the given json configuration file."""
        self.configuration = configuration
        self.admin_name = self.configuration['admin_name']
        self.survey_name = self.configuration['survey_name']
        self.survey_id = survey_id
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

    async def verify(self, verification_token):
        """Verify the user's email address and save submission as verified."""
        verification_time = now()
        if self.authentication != 'email':
            raise HTTPException(400, 'survey does not verify email addresses')
        if verification_time < self.start:
            raise HTTPException(400, 'survey is not open yet')
        if verification_time >= self.end:
            raise HTTPException(400, 'survey is closed')
        submission = await self.submissions.find_one(
            {'_id': verification_token},
        )
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
