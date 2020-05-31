import secrets
import time

from pymongo import DeleteMany, InsertOne
from fastapi import HTTPException
from starlette.responses import RedirectResponse

import credentials
import validation


FURL = credentials.FRONTEND_URL


class Survey:
    """The survey class that all surveys instantiate."""

    def __init__(
            self,
            identifier,
            database,
            template,
    ):
        self.id = identifier
        self.db = database
        self.start = template['start']
        self.end = template['end']
        self.validator = validation.create_validator(template)
    
    async def submit(self, submission):
        """Save a user submission in pending entries for verification."""
        timestamp = int(time.time())
        if timestamp < self.start:
            raise HTTPException(400, 'survey is not open yet')
        if timestamp >= self.end:
            raise HTTPException(400, 'survey is closed')
        if not self.validator.validate(submission):
            raise HTTPException(400, 'invalid submission')

        # TODO send verification email
        
        await self.db['pending'].insert_one({
            'survey': self.id,
            'email': submission['email'],
            'timestamp': timestamp,
            'token': secrets.token_hex(32),
            'properties': submission['properties'],
        })

    async def verify(self, token):
        """Verify user submission and move from it from pending to verified."""
        pending = await self.db['pending'].find_one({
            'survey': self.id,
            'token': token,
        })
        if pending is None:
            raise HTTPException(401, 'invalid token')
        del pending['token']
        requests = [
            DeleteMany({
                'email': pending['email'], 
                'survey': self.id,
            }),
            InsertOne(pending),
        ]
        await self.db['verified'].bulk_write(requests, ordered=True)
        return RedirectResponse(f'{FURL}/{self.id}/success')

    async def fetch(self):
        """Fetch and process the survey results."""
        submissions = self.db['verified'].find({'survey': self.id})
        results = {}
        async for sub in submissions:
            for pro in sub['properties'].keys():
                for option, choice in sub['properties'][pro]:
                    # TODO works only for boolean values
                    results[option] = results.get(option, 0) + choice
        return results
