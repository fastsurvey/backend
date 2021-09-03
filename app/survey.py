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

    def __init__(self, survey_id, username, configuration):
        """Create a survey from the given json configuration file."""
        self.survey_id = survey_id
        self.username = username
        self.configuration = configuration
        self.survey_name = self.configuration['survey_name']
        self.start = self.configuration['start']
        self.end = self.configuration['end']
        self.index = Survey._find_email_field_to_verify(self.configuration)
        self.submissions = database.database[
            f'surveys.{str(self.survey_id)}.submissions'
        ]
        self.unverified_submissions = database.database[
            f'surveys.{str(self.survey_id)}.unverified-submissions'
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
        submission_doc = await self.unverified_submissions.find_one(
            filter={'_id': auth.hash_token(verification_token)},
            projection={'_id': False},
        )
        if submission_doc is None:
            raise errors.InvalidVerificationTokenError()
        await self.submissions.replace_one(
            filter={'_id': submission_doc['submission'][str(self.index)]},
            replacement={
                'verification_time': verification_time,
                **submission_doc,
            },
            upsert=True,
        )
        return fastapi.responses.RedirectResponse(
            f'{settings.FRONTEND_URL}/{self.username}/{self.survey_name}'
            f'/success'
        )

    async def aggregate(self):
        """Query the survey submissions and return aggregated results."""
        return await aggregation.aggregate(self.submissions, self.configuration)


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
        x = utils.combine(username, survey_name)
        return self._cache[x]

    def update(self, survey_id, username, configuration):
        """Update or create survey object in the local cache."""
        x = utils.combine(username, configuration['survey_name'])
        self._cache[x] = Survey(survey_id, username, configuration)

    def delete(self, username, survey_name):
        """Remove survey object from the local cache."""
        x = utils.combine(username, survey_name)
        self._cache.pop(x, None)


################################################################################
# Functions To Manage Surveys
################################################################################


CACHE = SurveyCache()


async def fetch(username, survey_name, return_drafts=True):
    """Return the survey object corresponding to user and survey name."""
    try:
        survey = CACHE.fetch(username, survey_name)
    except KeyError:
        configuration = await database.database['configurations'].find_one(
            filter={'username': username, 'survey_name': survey_name},
            projection={'username': False},
        )
        if configuration is None:
            raise errors.SurveyNotFoundError()
        survey_id = configuration.pop('_id')
        CACHE.update(survey_id, username, configuration)
        survey = CACHE.fetch(username, survey_name)
    if survey.configuration['draft'] and not return_drafts:
        raise errors.SurveyNotFoundError()
    return survey


async def create(username, configuration):
    """Create a new survey configuration in the database and cache."""
    try:
        res = await database.database['configurations'].insert_one(
            document={'username': username, **configuration},
        )
    except pymongo.errors.DuplicateKeyError as error:
        index = str(error).split()[7]
        if index == 'username_survey_name_index':
            raise errors.SurveyNameAlreadyTakenError()
        else:
            raise errors.InternalServerError()
    CACHE.update(res.inserted_id, username, configuration)


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
        res = await database.database['configurations'].replace_one(
            filter={'_id': survey.survey_id},
            replacement={
                'username': username,
                **configuration,
            },
        )
    except pymongo.errors.DuplicateKeyError:
        raise errors.SurveyNameAlreadyTakenError()
    if res.matched_count == 0:
        raise errors.SurveyNotFoundError()
    CACHE.update(survey.survey_id, username, configuration)


async def reset(username, survey_name):
    """Delete all submission data but keep the configuration."""
    survey = await fetch(username, survey_name)
    await survey.submission.drop()
    await survey.unverified_submission.drop()


async def delete(username, survey_name):
    """Delete the survey and all its data from the database and cache."""
    survey = await fetch(username, survey_name)
    await database.database['configurations'].delete_one(
        filter={'_id': survey.survey_id},
    )
    CACHE.delete(username, survey_name)
    await survey.submission.drop()
    await survey.unverified_submission.drop()
