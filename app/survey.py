import secrets
import time
import os

from fastapi import HTTPException
from starlette.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError

from app.validation import SubmissionValidator
from app.results import Alligator


# frontend url
FURL = os.getenv('FURL')


class SurveyManager:
    """The manager manages creating, updating and deleting survey objects."""

    def __init__(self, database, letterbox):
        """Initialize this class with empty surveys dictionary."""
        self._database = database
        self._letterbox = letterbox
        self._cache = {}

    def _remember(self, configuration):
        """Update local survey cache with config-generated survey object."""
        self._cache.update({
            configuration['_id']: Survey(
                configuration,
                self._database,
                self._letterbox,
            )
        })

    def _forget(self, admin_name, survey_name):
        """Remove survey cache, either due to deletion or cache clearing."""
        raise NotImplementedError

    async def update(self, configuration):
        """Create or update the survey configuration in the database."""
        survey_id = configuration['_id']
        await self._database['configurations'].find_one_and_replace(
            filter={'_id': survey_id},
            replacement=configuration,
            upsert=True,
        )
        self._remember(configuration)

    async def fetch(self, admin_name, survey_name):
        """Return the survey object corresponding to admin and survey name."""
        survey_id = f'{admin_name}.{survey_name}'
        if survey_id not in self._cache:
            configuration = await self._database['configurations'].find_one(
                filter={'_id': survey_id},
            )
            if configuration is None:
                raise HTTPException(404, 'survey not found')
            self._remember(configuration)
        return self._cache[survey_id]

    async def clean(self, admin_name, survey_name):
        """Delete all the submission data of the survey from the database.

        We intentionally do not use self.get() here, as we want to delete
        the survey entry in self.purge() before calling self.clean()

        """
        survey_id = f'{admin_name}.{survey_name}'
        await self._database[f'{survey_id}.pending'].drop()
        await self._database[f'{survey_id}.verified'].drop()

    async def delete(self, admin_name, survey_name):
        """Delete the survey and all its data from the database and cache."""
        survey_id = f'{admin_name}.{survey_name}'
        await self._database['configurations'].delete_one({'_id': survey_id})
        self._cache.pop(survey_id, None)  # delete if present
        await self._database['results'].delete_one({'_id': survey_id})
        await self.clean(admin_name, survey_name)


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
        self.survey_id = f'{self.admin_name}.{self.survey_name}'
        self.title = self.configuration['title']
        self.start = self.configuration['start']
        self.end = self.configuration['end']
        self.validator = SubmissionValidator.create(self.configuration)
        self.letterbox = letterbox
        self.alligator = Alligator(self.configuration, database)
        self.pending = database[f'{self.survey_id}.pending']
        self.verified = database[f'{self.survey_id}.verified']
        self.results = None

    async def submit(self, submission):
        """Save a user submission in pending entries for verification."""
        timestamp = int(time.time())
        if timestamp < self.start:
            raise HTTPException(400, 'survey is not open yet')
        if timestamp >= self.end:
            raise HTTPException(400, 'survey is closed')
        if not self.validator.validate(submission):
            raise HTTPException(400, 'invalid submission')
        submission = {
            '_id': secrets.token_hex(32),
            'timestamp': timestamp,
            'properties': submission,
        }
        while True:
            try:
                await self.pending.insert_one(submission)
                break
            except DuplicateKeyError:
                submission['_id'] = secrets.token_hex(32)
        status = await self.letterbox.verify_email(
            self.admin_name,
            self.survey_name,
            self.title,
            'felix@felixboehm.dev',
            submission['_id'],
        )
        if status != 200:
            raise HTTPException(500, 'verification email delivery failure')

    async def verify(self, token):
        """Verify user submission and copy it from pending to verified."""
        timestamp = int(time.time())
        if timestamp < self.start:
            raise HTTPException(400, 'survey is not open yet')
        if timestamp >= self.end:
            raise HTTPException(400, 'survey is closed')
        pe = await self.pending.find_one({'_id': token})
        if pe is None:
            raise HTTPException(401, 'invalid token')
        ve = {
            '_id': pe['email'],
            'timestamp': timestamp,  # time is verify time, not submit time
            'properties': pe['properties'],
        }
        await self.verified.find_one_and_replace(
            filter={'_id': pe['email']},
            replacement=ve,
            upsert=True,
        )
        return RedirectResponse(
            f'{FURL}/{self.admin_name}/{self.survey_name}/success'
        )

    async def aggregate(self):
        """Query the survey submissions and return aggregated results."""
        timestamp = int(time.time())
        if timestamp < self.end:
            raise HTTPException(400, 'survey is not yet closed')
        self.results = self.results or await self.alligator.fetch()
        return self.results
