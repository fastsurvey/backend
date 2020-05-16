from pymongo import DeleteMany, InsertOne


class Survey:
    """The survey class that all surveys instantiate."""

    def __init__(
            self,
            identifier,
            database,
            schema,
    ):
        self.id = identifier
        self.db = database
        self.start = schema['start']
        self.end = schema['end']
        self.properties = schema['properties']

    @staticmethod
    def _validate_email(submission):
        """Validate the correct format of the mytum email."""
        if 'email' in submission and isinstance(submission['email'], str):
            parts = submission['email'].split('@')
            if len(parts) == 2:
                name, domain = parts
                if len(name) == 7 and domain == 'mytum.de':
                    return True
        return False

    def _validate_properties(self, submission):
        """Validate the property choices of the submission."""
        return False

    def validate(self, submission):
        """Validate the correct format of a user submission."""
        print('Submission validated successfully!')

    async def submit(self, submission):
        """Save a user submission in pending entries for verification."""
        self.validate(submission)
        print('Submission received successfully!')

    async def verify(self, token):
        """Verify user submission and move from it from pending to verified."""
        pending = await self.db['entries'].find_one({
            'token': token,
            'survey': self.id,
        })
        if pending is not None:
            del pending['token']
            requests = [
                DeleteMany({
                    'email': pending['email'], 
                    'survey': self.id,
                }),
                InsertOne(pending),
            ]
            await self.db['verified'].bulk_write(requests, ordered=True)

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


if __name__ == "__main__":

    st = [
        {'email': '123adsb@mytum.de'},
        {'email': '8383939@mytum.de'},
        {'email': 'FFFFFFF@mytum.de'},
    ]
    sf = [
        {},
        {'email': 'sadfj'},
        {'email': 12},
        {'email': 'a123ad@mytum.de'},
        {'email': 'a123ads@gmail.com'},
        {'email': '123@mytum.de@mytum.de'},
        {'email': None},
        {'emeeeeeel': '123adsb@mytum.de'},
    ]

    for s in st: 
        assert Survey._validate_email(s)
    for s in sf: 
        assert not Survey._validate_email(s)
