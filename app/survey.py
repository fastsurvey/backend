import pymongo.errors
import cachetools
import fastapi.responses

import app.validation as validation
import app.aggregation as aggregation
import app.utils as utils
import app.cryptography.verification as verification
import app.email as email
import app.settings as settings
import app.resources.database as database
import app.errors as errors


class SurveyManager:
    """The manager manages creating, updating and deleting surveys."""


    # TODO make distinction between frontend/backend configuration format
    # clearer, e.g. move exception handling into public functions and give
    # private functions only the finished configuration document as
    # argument.

    # or: split validation, errors, etc. and actual (e.g. update) logic
    # into public and private functions (might be useful in tests), same
    # for account.py


    def __init__(self):
        """Initialize a survey manager instance."""
        self.cache = SurveyCache()
        self.validator = validation.ConfigurationValidator()

    async def fetch(self, username, survey_name):
        """Return the survey object corresponding to user and survey name.

        Surveys drafts are not returned.

        """
        try:
            return self.cache.fetch(username, survey_name)
        except KeyError:
            configuration = await database.database['configurations'].find_one(
                filter={
                    'username': username,
                    'survey_name': survey_name,
                    'draft': False,
                },
                projection={'_id': False},
            )
            if configuration is None:
                raise errors.SurveyNotFoundError()
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

        The configuration includes the survey_name for consistency with the
        update() function. An exception will be raised if the survey_name in
        the route differs from the one specified in the configuration.

        """
        if survey_name != configuration['survey_name']:
            raise errors.InvalidConfigurationError()
        if not self.validator.validate(configuration):
            raise errors.InvalidConfigurationError()
        configuration['username'] = username
        try:
            await database.database['configurations'].insert_one(configuration)
            del configuration['_id']

            # TODO also delete the username from the configuration here?
            # like this the configuration in the survey is the same as
            # the one that is sent around in the routes

            self.cache.update(configuration)
        except pymongo.errors.DuplicateKeyError:
            raise errors.SurveyNameAlreadyTakenError()

    async def update(self, username, survey_name, configuration):
        """Update a survey configuration in the database and cache.

        Survey updates are only possible if the survey has not yet started.
        This means that the only thing to update in the database is the
        configuration, as there are no existing submissions or results.

        The configuration includes the survey_name despite it already being
        specified in the route. We do this in order to enable changing the
        survey_name.

        """

        # TODO make update only possible if survey has not yet started
        # -> no, if there are no submissions yet!

        if not self.validator.validate(configuration):
            raise errors.InvalidConfigurationError()
        configuration['username'] = username
        try:
            response = await database.database['configurations'].replace_one(
                filter={'username': username, 'survey_name': survey_name},
                replacement=configuration,
            )
        except pymongo.errors.DuplicateKeyError:
            raise errors.SurveyNameAlreadyTakenError()
        if response.matched_count == 0:
            raise errors.SurveyNotFoundError()
        self.cache.update(configuration)

    async def archive(self, username, survey_name):
        """Delete submission data of a survey, but keep the results."""
        survey_id = utils.combine(username, survey_name)
        await database.database[f'surveys.{survey_id}.submissions'].drop()
        s = f'surveys.{survey_id}.verified-submissions'
        await database.database[s].drop()

    async def reset(self, username, survey_name):
        """Delete all submission data including the results of a survey."""
        survey_id = utils.combine(username, survey_name)
        await database.database['resultss'].delete_one({'_id': survey_id})
        await database.database[f'surveys.{survey_id}.submissions'].drop()
        s = f'surveys.{survey_id}.verified-submissions'
        await database.database[s].drop()

    async def delete(self, username, survey_name):
        """Delete the survey and all its data from the database and cache."""
        await database.database['configurations'].delete_one(
            filter={'username': username, 'survey_name': survey_name},
        )
        self.cache.delete(username, survey_name)
        survey_id = utils.combine(username, survey_name)
        await database.database['resultss'].delete_one({'_id': survey_id})
        await database.database[f'surveys.{survey_id}.submissions'].drop()
        s = f'surveys.{survey_id}.verified-submissions'
        await database.database[s].drop()


class SurveyCache:
    """A cache layer for survey objects replacing by least recently used.

    When the survey is already cached, the time to get it is reduced by a
    factor of about 10.

    """

    def __init__(self):
        self._size = 2**10
        self._cache = cachetools.LRUCache(maxsize=self._size)

    def reset(self):
        """Reset the cache by removing all cached elements."""
        self._cache = cachetools.LRUCache(maxsize=self._size)

    def fetch(self, username, survey_name):
        """Fetch and return a survey object from the local cache.

        Raises KeyError if survey is not cached.

        """
        survey_id = utils.combine(username, survey_name)
        return self._cache[survey_id]

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
            self._cache[survey_id] = Survey(configuration)

    def delete(self, username, survey_name):
        """Remove survey object from the local cache."""
        survey_id = utils.combine(username, survey_name)
        self._cache.pop(survey_id, None)


class Survey:
    """The survey class that all surveys instantiate."""

    def __init__(self, configuration):
        """Create a survey from the given json configuration file."""
        self.configuration = configuration
        self.username = self.configuration['username']
        self.survey_name = self.configuration['survey_name']
        self.start = self.configuration['start']
        self.end = self.configuration['end']
        self.authentication = self.configuration['authentication']
        self.ei = Survey._get_email_field_index(self.configuration)
        self.validator = validation.SubmissionValidator.create(configuration)
        self.alligator = aggregation.Alligator(self.configuration)
        self.submissions = database.database[
            f'surveys'
            f'.{utils.combine(self.username, self.survey_name)}'
            f'.submissions'
        ]
        self.verified_submissions = database.database[
            f'surveys'
            f'.{utils.combine(self.username, self.survey_name)}'
            f'.verified-submissions'
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
        if submission_time < self.start or submission_time >= self.end:
            raise errors.SurveyDoesNotAcceptSubmissionsAtTheMomentError()
        if not self.validator.validate(submission):
            raise errors.InvalidSubmissionError()
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
                raise errors.InternalServerError()

    async def verify(self, verification_token):
        """Verify the user's email address and save submission as verified."""
        verification_time = utils.now()
        if self.authentication != 'email':
            raise errors.InvalidVerificationTokenError()
        if verification_time < self.start or verification_time >= self.end:
            raise errors.SurveyDoesNotAcceptSubmissionsAtTheMomentError()
        submission = await self.submissions.find_one(
            {'_id': verification_token},
        )
        if submission is None:
            raise errors.InvalidVerificationTokenError()
        submission['verification_time'] = verification_time
        submission['_id'] = submission['data'][str(self.ei + 1)]
        await self.verified_submissions.find_one_and_replace(
            filter={'_id': submission['_id']},
            replacement=submission,
            upsert=True,
        )
        return fastapi.responses.RedirectResponse(
            f'{settings.FRONTEND_URL}/{self.username}/{self.survey_name}'
            f'/success'
        )

    async def aggregate(self):
        """Query the survey submissions and return aggregated results."""
        if utils.now() < self.end:
            raise errors.NotImplementedError()
        self.results = self.results or await self.alligator.fetch()
        return self.results
