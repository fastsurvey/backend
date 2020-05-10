from abc import ABC, abstractmethod
from pymongo import DeleteMany, InsertOne


class Survey(ABC):
    
    def __init__(
            self,
            identifier,
            description,
            database,
    ):
        self.id = identifier
        self.description = description
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
    async def results(self):
        pass


class SingleChoiceSurvey(Survey):
    
    def __init__(
            self,
            identifier,
            description,
            database,
            choices,
    ):
        Survey.__init__(self, identifier, description, database)
        self.choices = choices
    
    async def validate(self):
        print('Submission validated!')

    async def submit(self):
        print('Submission received successfully!')

    async def results(self):
        print(f'Results: {self.choices[0]}: 60% vs. {self.choices[1]}: 40%!')
