import os
import asyncio
import fastapi
import starlette.responses
import pymongo.errors
import cachetools

import app.validation as validation
import app.aggregation as aggregation
import app.utils as utils
import app.cryptography.verification as verification
import app.cryptography.access as access
import app.email as email


# frontend url
FRONTEND_URL = os.getenv('FRONTEND_URL')


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
        self.cache = cachetools.LRUCache(maxsize=256)
        self.validator = validation.ConfigurationValidator()

    def _update_cache(self, configuration):
        """Update survey object in the local cache."""
        survey_id = utils.combine(
            configuration['username'],
            configuration['survey_name'],
        )
        self.cache[survey_id] = Survey(configuration, self.database)

    async def fetch(self, username, survey_name):
        """Return the survey object corresponding to user and survey name."""
        survey_id = utils.combine(username, survey_name)
        if survey_id not in self.cache:
            configuration = await self.database['configurations'].find_one(
                filter={'username': username, 'survey_name': survey_name},
                projection={'_id': False},
            )
            if configuration is None:
                raise fastapi.HTTPException(404, 'survey not found')
            self._update_cache(configuration)
        return self.cache[survey_id]

    async def fetch_configuration(self, username, survey_name):
        """Return survey configuration corresponding to user/survey name."""
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

            self._update_cache(configuration)
        except pymongo.errors.DuplicateKeyError:
            raise fastapi.HTTPException(400, 'survey exists')

    async def update(self, username, survey_name, configuration):
        """Update a survey configuration in the database and cache.

        Survey updates are only possible if the survey has not yet started.
        This means that the only thing to update in the database is the
        configuration, as there are no existing submissions or results.

        """

        # TODO make update only possible if survey has not yet started
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

        self._update_cache(configuration)

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
        survey_id = utils.combine(username, survey_name)
        if survey_id in self.cache:
            del self.cache[survey_id]
        await self.database['resultss'].delete_one({'_id': survey_id})
        await self.database[f'surveys.{survey_id}.submissions'].drop()
        await self.database[f'surveys.{survey_id}.verified-submissions'].drop()


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
            f'{FRONTEND_URL}/{self.username}/{self.survey_name}/success'
        )

    async def aggregate(self):
        """Query the survey submissions and return aggregated results."""
        if utils.now() < self.end:
            raise fastapi.HTTPException(400, 'survey is not yet closed')
        self.results = self.results or await self.alligator.fetch()
        return self.results
