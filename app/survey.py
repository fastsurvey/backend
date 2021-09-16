import pymongo.errors
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

            # Sending the submission verification email can fail (e.g. because
            # of an invalid email address). Nevertheless, we don't react to this
            # happening here as the author will be able to request a new
            # verification email in the future. In the case of an invalid
            # email address the submission will simply remain as a valid
            # unverified submission.

            await email.send_submission_verification(
                submission[str(self.index)],
                self.username,
                self.survey_name,
                self.configuration['title'],
                verification_token,
            )

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


    async def read_submissions(self):
        """Fetch all valid submissions."""
        cursor = self.submissions.aggregate(
            pipeline=[{'$replaceRoot': {'newRoot': '$submission'}}]
        )
        return await cursor.to_list(length=None)


################################################################################
# Functions To Manage Surveys
################################################################################


async def read(username, survey_name, return_drafts=True):
    """Return the survey object corresponding to user and survey name."""
    configuration = await database.database['configurations'].find_one(
        filter={'username': username, 'survey_name': survey_name},
        projection={'username': False},
    )
    if configuration is None:
        raise errors.SurveyNotFoundError()
    if configuration['draft'] and not return_drafts:
        raise errors.SurveyNotFoundError()
    survey_id = configuration.pop('_id')
    return Survey(survey_id, username, configuration)


async def create(username, configuration):
    """Create a new survey configuration in the database."""
    for i, field in enumerate(configuration['fields']):
        if field['identifier'] != i:
            raise errors.InvalidSyntaxError()
    try:
        await database.database['configurations'].insert_one(
            document={
                'username': username,
                'max_identifier': configuration['fields'][-1]['identifier'],
                **configuration,
            },
        )
    except pymongo.errors.DuplicateKeyError as error:
        index = str(error).split()[7]
        if index == 'username_survey_name_index':
            raise errors.SurveyNameAlreadyTakenError()
        else:
            raise errors.InternalServerError()


async def update(username, survey_name, configuration):
    """Update a survey configuration in the database.

    Survey updates are possible even if the survey already has submissions.
    This works by assigning each field an identifier that is unique over the
    lifetime of the survey. During updates, new fields are assigned a new
    identifier. Changes to individual fields do not affect their identifier.
    Changes to the field type necessitate a new identifier.

    The configuration includes the survey_name despite it already being
    specified in the route. We do this in order to enable changing the
    survey_name.

    """
    survey = await read(username, survey_name)

    def identifiers(configuration):
        return {field['identifier'] for field in configuration['fields']}

    # check that fields with unchanged identifier have the same field type
    for x in configuration['fields']:
        for y in survey.configuration['fields']:
            if x['identifier'] == y['identifier'] and x['type'] != y['type']:
                raise errors.InvalidSyntaxError()

    # check that new fields are numbered in ascending order
    new = identifiers(configuration) - identifiers(survey.configuration)
    for i, e in enumerate(sorted(new)):
        if e != survey.max_identifier + i + 1:
            raise errors.InvalidSyntaxError()

    # write changes to database
    try:
        res = await database.database['configurations'].replace_one(
            filter={
                '_id': survey.survey_id,
                # this ensures that even when the configuration changed
                # between read and write, that only valid updates are written
                'max_identifier': survey.max_identifier,
            },
            replacement={
                'username': username,
                'max_identifier': max(identifiers(configuration)),
                **configuration,
            },
        )
    except pymongo.errors.DuplicateKeyError as error:
        index = str(error).split()[7]
        if index == 'username_survey_name_index':
            raise errors.SurveyNameAlreadyTakenError()
        else:
            raise errors.InternalServerError()
    if res.matched_count == 0:
        raise errors.InvalidSyntaxError()


async def reset(username, survey_name):
    """Delete all submission data but keep the survey configuration."""
    survey = await read(username, survey_name)
    async with await database.client.start_session() as session:
        async with session.start_transaction():
            await survey.submissions.drop()
            await survey.unverified_submissions.drop()


async def delete(username, survey_name):
    """Delete the survey and all its data from the database."""
    survey = await read(username, survey_name)
    async with await database.client.start_session() as session:
        async with session.start_transaction():
            await database.database['configurations'].delete_one(
                filter={'_id': survey.survey_id},
            )
            await survey.submissions.drop()
            await survey.unverified_submissions.drop()
