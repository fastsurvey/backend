from abc import ABC, abstractmethod
from pymongo import DeleteMany, InsertOne


class Survey(ABC):
    
    def __init__(
            self,
            identifier,
            title,
            database,
    ):
        self.id = identifier
        self.title = title
        self.db = database

    @abstractmethod
    async def validate(self, submission):
        """Validate the correct format of a user submission."""
        pass

    @abstractmethod
    async def submit(self, submission):
        """Receive a user submission and save it in the pending entries
        collection to be verified.

        """
        pass

    async def verify(self, token):
        """Verify user submission by searching the corresponding user entry in 
        the pending entries collection and moving it to verified entries.

        """
        pending = await self.db['pending_entries'].find_one({
            'verification_token': token,
            'survey': self.id,
        })
        if pending is not None:
            del pending['verification_token']
            requests = [
                DeleteMany({
                    'email': pending['email'], 
                    'survey': self.id,
                }),
                InsertOne(pending),
            ]
            await self.db['verified_entries'].bulk_write(requests, ordered=True)

    @abstractmethod
    async def fetch(self):
        """Fetch and process the survey results"""
        pass


class ChoiceSurvey(Survey):
    
    def __init__(
            self,
            identifier,
            title,
            database,
    ):
        Survey.__init__(self, identifier, title, database)
        # TODO add attributes as needed

    async def validate(self):
        print('Submission validated!')

    async def submit(self):
        print('Submission received successfully!')

    async def fetch(self):
        submissions = self.db['verified_entries'].find({'survey': self.id})
        results = {}
        async for sm in submissions:
            for choice, answer in sm['election'].items():
                results[choice] = results.get(choice, 0) + answer
        return results
