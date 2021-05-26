import fastapi
import pymongo.errors
import cachetools

import app.validation as validation
import app.aggregation as aggregation
import app.utils as utils
import app.cryptography.verification as verification
import app.email as email
import app.settings as settings


class SurveyManager:
    """The manager manages creating, updating and deleting surveys."""


    # TODO make distinction between frontend/backend configuration format
    # clearer, e.g. move exception handling into public functions and give
    # private functions only the finished configuration document as
    # argument.

    # or: split validation, errors, etc. and actual (e.g. update) logic
    # into public and private functions (might be useful in tests), same
    # for account.py


    def __init__(self, database):
        """Initialize a survey manager instance."""
        self.database = database
        self.cache = SurveyCache(database)
        self.validator = validation.ConfigurationValidator()

    async def fetch(self, username, survey_name):
        """Return the survey object corresponding to user and survey name.

        Surveys drafts are not returned.

        """
        try:
            return self.cache.fetch(username, survey_name)
        except KeyError:
            configuration = await self.database['configurations'].find_one(
                filter={
                    'username': username,
                    'survey_name': survey_name,
                    'draft': False,
                },
                projection={'_id': False},
            )
            if configuration is None:
                raise fastapi.HTTPException(404, 'survey not found')
            self.cache.update(configuration)
            return self.cache.fetch(username, survey_name)

    async def fetch_configuration(self, username, survey_name):
        """Return survey configuration corresponding to user/survey name.

        Draft configurations are not returned.

        """
        survey = await self.fetch(username, survey_name)
        return {
            key: survey.configuration[key]
            for key
            in survey.configuration.keys()
            if key not in ['username']
        }

    async def create(self, username, survey_name, configuration):
        """Create a new survey configuration in the database and cache.

        The configuration includes the survey_name despite it already being
        specified in the route. We do this in order to enable changing the
        survey_name.

        """
        if survey_name != configuration['survey_name']:
            raise fastapi.HTTPException(400, 'invalid configuration')
        if not self.validator.validate(configuration):
            raise fastapi.HTTPException(400, 'invalid configuration')
        configuration['username'] = username
        try:
            await self.database['configurations'].insert_one(configuration)
            del configuration['_id']

            # TODO also delete the username from the configuration here?
            # like this the configuration in the survey is the same as
            # the one that is sent around in the routes

            self.cache.update(configuration)
        except pymongo.errors.DuplicateKeyError:
            raise fastapi.HTTPException(400, 'survey exists')

    async def update(self, username, survey_name, configuration):
        """Update a survey configuration in the database and cache.

        Survey updates are only possible if the survey has not yet started.
        This means that the only thing to update in the database is the
        configuration, as there are no existing submissions or results.

        """

        # TODO make update only possible if survey has not yet started
        # -> no, if there are no submissions yet!
        # TODO when survey name ist changed to something that exists already
        # it'll probably fail due to the index, but that must be handled

        if not self.validator.validate(configuration):
            raise fastapi.HTTPException(400, 'invalid configuration')
        configuration['username'] = username
        result = await self.database['configurations'].replace_one(
            filter={'username': username, 'survey_name': survey_name},
            replacement=configuration,
        )
        if result.matched_count == 0:
            raise fastapi.HTTPException(400, 'not an existing survey')

        assert '_id' not in configuration.keys()
        assert '_id' in configuration.keys()

        self.cache.update(configuration)

    async def _archive(self, username, survey_name):
        """Delete submission data of a survey, but keep the results."""
        survey_id = utils.combine(username, survey_name)
        await self.database[f'surveys.{survey_id}.submissions'].drop()
        await self.database[f'surveys.{survey_id}.verified-submissions'].drop()

    async def reset(self, username, survey_name):
        """Delete all submission data including the results of a survey."""
        survey_id = utils.combine(username, survey_name)
        await self.database['resultss'].delete_one({'_id': survey_id})
        await self.database[f'surveys.{survey_id}.submissions'].drop()
        await self.database[f'surveys.{survey_id}.verified-submissions'].drop()

    async def delete(self, username, survey_name):
        """Delete the survey and all its data from the database and cache."""
        await self.database['configurations'].delete_one(
            filter={'username': username, 'survey_name': survey_name},
        )
        self.cache.delete(username, survey_name)
        survey_id = utils.combine(username, survey_name)
        await self.database['resultss'].delete_one({'_id': survey_id})
        await self.database[f'surveys.{survey_id}.submissions'].drop()
        await self.database[f'surveys.{survey_id}.verified-submissions'].drop()


class SurveyCache:
    """A cache layer for survey objects operating by LRU."""

    def __init__(self, database):
        self.cache = cachetools.LRUCache(maxsize=2**10)
        self.database = database

    def fetch(self, username, survey_name):
        """Fetch and return a survey object from the local cache."""
        survey_id = utils.combine(username, survey_name)
        return self.cache[survey_id]

    def update(self, configuration):
        """Update or create survey object in the local cache.

        Draft surveys are not cached. When the given configuration is a draft,
        any (non-draft) configuration is deleted from the cache.

        """
        username = configuration['username']
        survey_name = configuration['survey_name']
        survey_id = utils.combine(username, survey_name)
        if configuration['draft']:
            self.delete(username, survey_name)
        else:
            self.cache[survey_id] = Survey(configuration, self.database)

    def delete(self, username, survey_name):
        """Remove survey object from the local cache."""
        survey_id = utils.combine(username, survey_name)
        self.cache.pop(survey_id, None)


class Survey:
    """The survey class that all surveys instantiate."""

    def __init__(
            self,
            configuration,
            database,
    ):
        """Create a survey from the given json configuration file."""
        self.configuration = configuration
        self.username = self.configuration['username']
        self.survey_name = self.configuration['survey_name']
        self.start = self.configuration['start']
        self.end = self.configuration['end']
        self.authentication = self.configuration['authentication']
        self.ei = Survey._get_email_field_index(self.configuration)
        self.validator = validation.SubmissionValidator.create(configuration)
        self.alligator = aggregation.Alligator(self.configuration, database)
        self.submissions = database[
            f'surveys'
            f'.{utils.combine(self.username, self.survey_name)}'
            f'.submissions'
        ]
        self.verified_submissions = database[
            f'surveys'
            f'.{utils.combine(self.username, self.survey_name)}'
            f'.submissions.verified'
        ]
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
        submission_time = utils.now()
        if submission_time < self.start:
            raise fastapi.HTTPException(400, 'survey is not open yet')
        if submission_time >= self.end:
            raise fastapi.HTTPException(400, 'survey is closed')
        if not self.validator.validate(submission):
            raise fastapi.HTTPException(400, 'invalid submission')
        submission = {
            'submission_time': submission_time,
            'data': submission,
        }
        if self.authentication == 'open':
            await self.submissions.insert_one(submission)
        if self.authentication == 'email':
            submission['_id'] = verification.token()
            while True:
                try:
                    await self.submissions.insert_one(submission)
                    break
                except pymongo.errors.DuplicateKeyError:
                    submission['_id'] = verification.token()
            status = await email.send_submission_verification(
                submission['data'][str(self.ei + 1)],
                self.username,
                self.survey_name,
                self.configuration['title'],
                submission['_id'],
            )
            if status != 200:
                raise fastapi.HTTPException(500, 'email delivery failure')

    async def verify(self, verification_token):
        """Verify the user's email address and save submission as verified."""
        verification_time = utils.now()
        if self.authentication != 'email':
            raise fastapi.HTTPException(400, 'survey is not of type email')
        if verification_time < self.start:
            raise fastapi.HTTPException(400, 'survey is not open yet')
        if verification_time >= self.end:
            raise fastapi.HTTPException(400, 'survey is closed')
        submission = await self.submissions.find_one(
            {'_id': verification_token},
        )
        if submission is None:
            raise fastapi.HTTPException(401, 'invalid verification token')
        submission['verification_time'] = verification_time
        submission['_id'] = submission['data'][str(self.ei + 1)]
        await self.verified_submissions.find_one_and_replace(
            filter={'_id': submission['_id']},
            replacement=submission,
            upsert=True,
        )
        return fastapi.RedirectResponse(
            f'{settings.FRONTEND_URL}/{self.username}/{self.survey_name}'
            f'/success'
        )

    async def aggregate(self):
        """Query the survey submissions and return aggregated results."""
        if utils.now() < self.end:
            raise fastapi.HTTPException(400, 'survey is not yet closed')
        self.results = self.results or await self.alligator.fetch()
        return self.results
