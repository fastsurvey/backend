import secrets
import time

from pymongo import DeleteMany, InsertOne
from fastapi import HTTPException
from starlette.responses import RedirectResponse

import credentials
import validation
import mailing


FURL = credentials.FRONTEND_URL


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
        await self.pending.insert_one(submission)

        # TODO use token as primary key, to explicitly avoid token collisions
        # TODO send verification email
        # email sending needs to be somehow mocked (and tested) in the tests

    async def verify(self, token):
        """Verify user submission and move from it from pending to verified."""
        pe = await self.pending.find_one({'_id': token})
        if pe is None:
            raise HTTPException(401, 'invalid token')
        ve = {
            '_id': pe['email'],
            'timestamp': pe['timestamp'],
            'properties': pe['properties'],
        }
        requests = [
            DeleteMany({
                '_id': pe['email'], 
            }),
            InsertOne(ve),
        ]
        await self.verified.bulk_write(requests, ordered=True)
        return RedirectResponse(f'{FURL}/{self.name}/success')

    async def fetch(self):
        """Fetch and process the survey results."""
        submissions = self.verified.find()
        results = {}
        async for sb in submissions:
            for pp in sb['properties'].keys():
                for option, choice in sb['properties'][pp]:
                    # TODO works only for boolean values
                    results[option] = results.get(option, 0) + choice
        return results
