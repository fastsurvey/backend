import secrets
import time
import os

from fastapi import HTTPException
from starlette.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError

from app.validation import SubmissionValidator
from app.mailing import Postman
from app.results import Alligator


# frontend url
FURL = os.getenv('FURL')


class SurveyManager:
    """The manager manages creating, updating and deleting survey objects."""

    def __init__(self, database, postmark):
        """Initialize this class with empty surveys dictionary."""
        self.database = database
        self.postmark = postmark
        self.surveys = {}

    def add(self, configuration):
        """Add new survey object via translation of given configuration."""
        self.surveys.update({
            configuration['_id']: Survey(
                configuration,
                self.database,
                self.postmark,
            )
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
            postmark,
    ):
        """Create a survey from the given json configuration file."""
        self.cn = configuration
        self.admin = self.cn['admin']
        self.name = self.cn['name']
        self.start = self.cn['start']
        self.end = self.cn['end']
        self.validator = SubmissionValidator.create(self.cn)
        self.postman = Postman(self.cn, postmark)
        self.alligator = Alligator(self.cn, database)
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

        '''

        try:
            self.postman.on_submit(submission)
        except Exception as e:
            print(e)
            raise HTTPException(500, 'verification email delivery failure')

        '''


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
