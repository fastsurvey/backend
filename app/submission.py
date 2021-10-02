import pymongo

import app.errors as errors
import app.utils as utils
import app.survey as survey
import app.auth as auth
import app.email as email
import app.models as models


async def submit(username, survey_name, submission):
    """Save a user's submission in the submissions collection."""
    configuration = await survey.read(username, survey_name)
    if configuration['draft']:
        raise errors.SurveyNotFoundError()
    timestamp = utils.now()
    start, end = configuration['start'], configuration['end']
    if start is not None and timestamp < start:
        raise errors.InvalidTimingError()
    if end is not None and timestamp >= end:
        raise errors.InvalidTimingError()

    # check submission format
    Submission = models.build_submission_model(configuration)
    Submission(**submission)

    # save submission and send verification email if email is to be verified
    submissions = survey.submissions_from_configuration(configuration)
    for field in configuration['fields']:
        if field['type'] == 'email' and field['verify']:
            verification_token = auth.generate_token()
            while True:
                try:
                    await submissions.insert_one(
                        document={
                            '_id': auth.hash_token(verification_token),
                            'submission_time': timestamp,
                            'verified': False,
                            'submission': submission,
                        }
                    )
                    break
                except pymongo.errors.DuplicateKeyError:
                    verification_token = auth.generate_token()

            # Sending the submission verification email can fail (e.g. because
            # of an invalid email address). Nevertheless, we don't react to this
            # happening here. Maybe the author will be able to request a new
            # verification email in the future. In the case of an invalid email
            # address the submission will simply remain as a valid unverified
            # submission.

            await email.send_submission_verification(
                submission[str(field['identifier'])],
                username,
                survey_name,
                configuration['title'],
                verification_token,
            )
            break
    else:
        await submissions.insert_one(
            document={
                'submission_time': timestamp,
                'submission': submission,
            }
        )


async def verify(username, survey_name, verification_token):
    """Verify the user's email address and save the submission as verified."""
    configuration = await survey.read(username, survey_name)
    if configuration['draft']:
        raise errors.SurveyNotFoundError()
    timestamp = utils.now()
    start, end = configuration['start'], configuration['end']
    if start is not None and timestamp < start:
        raise errors.InvalidTimingError()
    if end is not None and timestamp >= end:
        raise errors.InvalidTimingError()

    # find submission by its verification token and mark it as verified
    submissions = survey.submissions_from_configuration(configuration)
    res = await submissions.update_one(
        filter={'_id': auth.hash_token(verification_token)},
        update={
            '$set': {
                'verification_time': timestamp,
                'verified': True,
            },
        },
    )
    if res.matched_count == 0:
        raise errors.InvalidVerificationTokenError()
