import pymongo.errors
import cachetools
import fastapi.responses

import app.aggregation as aggregation
import app.utils as utils
import app.cryptography.verification as verification
import app.email as email
import app.settings as settings
import app.resources.database as database
import app.errors as errors
import app.models as models


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

    async def fetch(self, username, survey_name, return_drafts=True):
        """Return the survey object corresponding to user and survey name."""
        try:
            return self.cache.fetch(username, survey_name)
        except KeyError:
            configuration = await database.database['configurations'].find_one(
                filter={
                    'username': username,
                    'survey_name': survey_name,
                },
                projection={'_id': False},
            )
            if configuration is None:
                raise errors.SurveyNotFoundError()
            if configuration['draft'] and not return_drafts:
                raise errors.SurveyNotFoundError()
            self.cache.update(configuration)
            return self.cache.fetch(username, survey_name)

    async def fetch_configuration(
            self,
            username,
            survey_name,
            return_drafts=True,
        ):
        """Return survey configuration corresponding to user/survey name."""
        survey = await self.fetch(username, survey_name, return_drafts)
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

        Survey updates are only possible if the survey has no submissions yet.
        This is to ensure that submissions cannot be invalidated and means
        that the only thing to update in the database is the configuration.

        The configuration includes the survey_name despite it already being
        specified in the route. We do this in order to enable changing the
        survey_name.

        """
        survey = await self.fetch(username, survey_name)
        counter = await survey.submissions.count_documents({})
        counter += await survey.unverified_submissions.count_documents({})
        if counter > 0:
            raise errors.SubmissionsExistError()
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

    async def reset(self, username, survey_name):
        """Delete all submission data but keep the configuration."""
        self.cache.delete(username, survey_name)
        x = f'surveys.{utils.combine(username, survey_name)}'
        await database.database[f'{x}.submissions'].drop()
        await database.database[f'{x}.unverified-submissions'].drop()

    async def delete(self, username, survey_name):
        """Delete the survey and all its data from the database and cache."""
        await database.database['configurations'].delete_one(
            filter={'username': username, 'survey_name': survey_name},
        )
        self.cache.delete(username, survey_name)
        x = f'surveys.{utils.combine(username, survey_name)}'
        await database.database[f'{x}.submissions'].drop()
        await database.database[f'{x}.unverified-submissions'].drop()


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
        self.index = Survey._find_email_field_to_verify(self.configuration)
        self.submissions = database.database[
            f'surveys.{utils.identify(self.configuration)}'
            f'.submissions'
        ]
        self.unverified_submissions = database.database[
            f'surveys.{utils.identify(self.configuration)}'
            f'.unverified-submissions'
        ]
        self.Submission = models.build_submission_model(configuration)

    @staticmethod
    def _find_email_field_to_verify(configuration):
        """Find index of potential email field to verify in configuration."""
        for index, field in enumerate(configuration['fields']):
            if field['type'] == 'email' and field['verify']:
                return index
        return None

    async def submit(self, submission):
        """Save a user submission in the submissions collection."""
        submission_time = utils.now()
        if submission_time < self.start or submission_time >= self.end:
            raise errors.InvalidTimingError()
        submission = {
            'submission_time': submission_time,
            'data': submission,
        }
        if self.index is None:
            await self.submissions.insert_one(submission)
        else:
            submission['_id'] = verification.token()
            while True:
                try:
                    await self.unverified_submissions.insert_one(submission)
                    break
                except pymongo.errors.DuplicateKeyError:
                    submission['_id'] = verification.token()
            status = await email.send_submission_verification(
                submission['data'][str(self.index)],
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
        if self.index is None:
            raise errors.InvalidVerificationTokenError()
        if verification_time < self.start or verification_time >= self.end:
            raise errors.InvalidTimingError()
        submission = await self.unverified_submissions.find_one(
            {'_id': verification_token},
        )
        if submission is None:
            raise errors.InvalidVerificationTokenError()
        submission['verification_time'] = verification_time
        submission['_id'] = submission['data'][str(self.index)]
        await self.submissions.find_one_and_replace(
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
        return await aggregation.aggregate(self.configuration)
