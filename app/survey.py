import pymongo.errors
import cachetools
import fastapi.responses

import app.aggregation as aggregation
import app.utils as utils
import app.email as email
import app.settings as settings
import app.resources.database as database
import app.errors as errors
import app.models as models
import app.authentication as auth


################################################################################
# Survey Class
################################################################################


class Survey:
    """The survey class that all surveys instantiate."""

    def __init__(self, username, configuration):
        """Create a survey from the given json configuration file."""
        self.username = username
        self.configuration = configuration
        self.survey_name = self.configuration['survey_name']
        self.start = self.configuration['start']
        self.end = self.configuration['end']
        self.index = Survey._find_email_field_to_verify(self.configuration)
        self.submissions = database.database[
            f'surveys.{utils.identify(self.username, self.configuration)}'
            f'.submissions'
        ]
        self.unverified_submissions = database.database[
            f'surveys.{utils.identify(self.username, self.configuration)}'
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
        if self.index is None:
            await self.submissions.insert_one(
                document={
                    'submission_time': submission_time,
                    'submission': submission,
                }
            )
        else:
            verification_token = auth.generate_token()
            while True:
                try:
                    await self.unverified_submissions.insert_one(
                        document={
                            '_id': auth.hash_token(verification_token),
                            'submission_time': submission_time,
                            'submission': submission,
                        }
                    )
                    break
                except pymongo.errors.DuplicateKeyError:
                    verification_token = auth.generate_token()
            status = await email.send_submission_verification(
                submission[str(self.index)],
                self.username,
                self.survey_name,
                self.configuration['title'],
                verification_token,
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

        """
        submission_doc = await self.unverified_submissions.find_one(
            filter={'_id': auth.hash_token(verification_token)},
            projection={'_id': False},
        )
        if submission_doc is None:
            raise errors.InvalidVerificationTokenError()
        email_address = submission_doc['submission'][str(self.index)]
        await self.submissions.replace_one(
            filter={'_id': email_address},
            replacement={
                '_id': email_address,
                'verification_time': verification_time,
                **submission_doc,
            },
            upsert=True,
        )
        """

        submission = await self.unverified_submissions.find_one(
            {'_id': auth.hash_token(verification_token)},
        )
        if submission is None:
            raise errors.InvalidVerificationTokenError()
        submission['verification_time'] = verification_time
        submission['_id'] = submission['submission'][str(self.index)]
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
        return await aggregation.aggregate(self.username, self.configuration)


################################################################################
# Cache Layer
################################################################################


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

    def update(self, username, configuration):
        """Update or create survey object in the local cache."""
        survey_id = utils.identify(username, configuration)
        self._cache[survey_id] = Survey(username, configuration)

    def delete(self, username, survey_name):
        """Remove survey object from the local cache."""
        survey_id = utils.combine(username, survey_name)
        self._cache.pop(survey_id, None)


################################################################################
# Functions To Manage Surveys
################################################################################


CACHE = SurveyCache()


async def fetch(username, survey_name, return_drafts=True):
    """Return the survey object corresponding to user and survey name."""
    try:
        return CACHE.fetch(username, survey_name)
    except KeyError:
        configuration = await database.database['configurations'].find_one(
            filter={'username': username, 'survey_name': survey_name},
            projection={'_id': False, 'username': False},
        )
        if configuration is None:
            raise errors.SurveyNotFoundError()
        if configuration['draft'] and not return_drafts:
            raise errors.SurveyNotFoundError()
        CACHE.update(username, configuration)
        return CACHE.fetch(username, survey_name)


async def create(username, configuration):
    """Create a new survey configuration in the database and cache."""
    try:
        await database.database['configurations'].insert_one(
            document={'username': username, **configuration},
        )
    except pymongo.errors.DuplicateKeyError:
        raise errors.SurveyNameAlreadyTakenError()
    CACHE.update(username, configuration)


async def update(username, survey_name, configuration):
    """Update a survey configuration in the database and cache.

    Survey updates are only possible if the survey has no submissions yet.
    This is to ensure that submissions cannot be invalidated and means
    that the only thing to update in the database is the configuration.

    The configuration includes the survey_name despite it already being
    specified in the route. We do this in order to enable changing the
    survey_name.

    """
    survey = await fetch(username, survey_name)
    counter = await survey.submissions.count_documents({})
    counter += await survey.unverified_submissions.count_documents({})
    if counter > 0:
        raise errors.SubmissionsExistError()
    try:
        response = await database.database['configurations'].replace_one(
            filter={'username': username, 'survey_name': survey_name},
            replacement={'username': username, **configuration},
        )
    except pymongo.errors.DuplicateKeyError:
        raise errors.SurveyNameAlreadyTakenError()
    if response.matched_count == 0:
        raise errors.SurveyNotFoundError()
    CACHE.update(username, configuration)


async def reset(username, survey_name):
    """Delete all submission data but keep the configuration."""
    x = f'surveys.{utils.combine(username, survey_name)}'
    await database.database[f'{x}.submissions'].drop()
    await database.database[f'{x}.unverified-submissions'].drop()


async def delete(username, survey_name):
    """Delete the survey and all its data from the database and cache."""
    await database.database['configurations'].delete_one(
        filter={'username': username, 'survey_name': survey_name},
    )
    CACHE.delete(username, survey_name)
    x = f'surveys.{utils.combine(username, survey_name)}'
    await database.database[f'{x}.submissions'].drop()
    await database.database[f'{x}.unverified-submissions'].drop()
