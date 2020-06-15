import secrets
import time

from fastapi import HTTPException
from starlette.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError

import credentials
import validation
import mailing
import results


FURL = credentials.FRONTEND_URL


class SurveyManager:
    """The manager manages creating, updating and deleting survey objects."""

    def __init__(self, database):
        """Initialize this class with empty suveys dictionary."""
        self.database = database
        self.surveys = {}

    def add(self, configuration):
        """Add new survey object via translation of given configuration."""
        self.surveys.update({
            configuration['_id']: Survey(configuration, self.database)
        })

    async def get(self, admin, survey):
        """Return the survey object corresponding to the given identifiers."""
        identifier = f'{admin}.{survey}'
        if identifier not in self.surveys:
            cn = await self.database['configurations'].find_one(
                {'_id': identifier},
            )
            if cn is None:
                raise HTTPException(404, 'survey not found')
            # due to await, check again to make sure add is only run once
            if identifier not in self.surveys:
                self.add(cn)
        return self.surveys[identifier]


class Survey:
    """The survey class that all surveys instantiate."""

    def __init__(
            self,
            configuration,
            database,
    ):
        """Create a survey from the given json configuration file."""
        self.cn = configuration
        self.admin = self.cn['admin']
        self.name = self.cn['name']
        self.start = self.cn['start']
        self.end = self.cn['end']
        self.validator = validation.SubmissionValidator.create(self.cn)
        self.postman = mailing.Postman(self.cn)
        self.alligator = results.Alligator(self.cn, database)
        self.pending = database[f'{self.admin}.{self.name}.pending']
        self.verified = database[f'{self.admin}.{self.name}.verified']

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
            'email': submission['email'],
            'timestamp': timestamp,
            'properties': submission['properties'],
        }
        while True:
            try: 
                await self.pending.insert_one(submission)
                break
            except DuplicateKeyError: 
                submission['_id'] = secrets.token_hex(32)

        # TODO send verification email
        # email sending needs to be somehow mocked (and tested) in the tests

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
        return RedirectResponse(f'{FURL}/{self.admin}/{self.name}/success')

    async def fetch(self):
        """Query the survey submissions and return aggregated results."""
        return await self.alligator.fetch()
