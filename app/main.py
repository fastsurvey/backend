import fastapi
import fastapi.middleware.cors
import pydantic

import app.account as ac
import app.survey as sv
import app.documentation as docs
import app.settings as settings
import app.validation as validation
import app.authentication as auth


# create fastapi app
app = fastapi.FastAPI(
    title='FastSurvey',
    version='0.2.0',
    docs_url='/documentation/swagger',
    redoc_url='/documentation/redoc',
)
# configure cross-origin resource sharing
app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)
# instantiate survey manager
survey_manager = sv.SurveyManager()
# instantiate account manager
account_manager = ac.AccountManager(survey_manager)


# add pydantic ValidationError exception handler
@app.exception_handler(pydantic.ValidationError)
async def validation_error_exception_handler(request, exc):
    return fastapi.responses.JSONResponse(
        status_code=422,
        content={'detail': fastapi.encoders.jsonable_encoder(exc.errors())}
    )


################################################################################
# Routes
################################################################################


@app.get(**docs.SPECIFICATIONS['server_status'])
async def server_status():
    """Return some information about the server."""
    return dict(
        commit_sha=settings.COMMIT_SHA,
        branch_name=settings.BRANCH_NAME,
        start_time=settings.START_TIME,
    )


@app.get(**docs.SPECIFICATIONS['fetch_user'])
@auth.authorize
async def fetch_user(
        data: validation.FetchUserRequestData = fastapi.Depends(),
    ):
    """Fetch the given user's account data."""
    return await account_manager.fetch(data.username)


@app.post(**docs.SPECIFICATIONS['create_user'])
async def create_user(
        data: validation.CreateUserRequestData = fastapi.Depends(),
    ):
    """Create a new user based on the given account data."""
    await account_manager.create(data.account_data.dict())


@app.put(**docs.SPECIFICATIONS['update_user'])
@auth.authorize
async def update_user(
        data: validation.UpdateUserRequestData = fastapi.Depends(),
    ):
    """Update the given user's account data."""
    await account_manager.update(data.username, data.account_data.dict())


@app.delete(**docs.SPECIFICATIONS['delete_user'])
@auth.authorize
async def delete_user(
        data: validation.DeleteUserRequestData = fastapi.Depends(),
    ):
    """Delete the user and all their surveys from the database."""
    await account_manager.delete(data.username)


@app.get(**docs.SPECIFICATIONS['fetch_surveys'])
@auth.authorize
async def fetch_surveys(
        data: validation.FetchSurveysRequestData = fastapi.Depends(),
    ):
    """Fetch the user's survey configurations sorted by the start date.

    As this is a protected route, configurations of surveys that are in
    draft mode **are** returned.

    """
    return await account_manager.fetch_configurations(
        data.username,
        data.skip,
        data.limit,
    )


@app.get(**docs.SPECIFICATIONS['fetch_survey'])
async def fetch_survey(
        data: validation.FetchSurveyRequestData = fastapi.Depends(),
    ):
    """Fetch a survey configuration.

    As this is an unprotected route, configurations of surveys that are in
    draft mode **are not** returned.

    """
    return await survey_manager.fetch_configuration(
        data.username,
        data.survey_name,
        return_drafts=False,
    )


@app.post(**docs.SPECIFICATIONS['create_survey'])
@auth.authorize
async def create_survey(
        data: validation.CreateSurveyRequestData = fastapi.Depends(),
    ):
    """Create new survey with given configuration."""
    await survey_manager.create(
        data.username,
        data.survey_name,
        data.configuration.dict(by_alias=True),
    )


@app.put(**docs.SPECIFICATIONS['update_survey'])
@auth.authorize
async def update_survey(
        data: validation.UpdateSurveyRequestData = fastapi.Depends(),
    ):
    """Update survey with given configuration."""
    await survey_manager.update(
        data.username,
        data.survey_name,
        data.configuration.dict(by_alias=True),
    )


@app.delete(**docs.SPECIFICATIONS['reset_survey'])
@auth.authorize
async def reset_survey(
        data: validation.ResetSurveyRequestData = fastapi.Depends(),
    ):
    """Reset a survey by deleting all submission data including any results."""
    await survey_manager.reset(data.username, data.survey_name)


@app.delete(**docs.SPECIFICATIONS['delete_survey'])
@auth.authorize
async def delete_survey(
        data: validation.DeleteSurveyRequestData = fastapi.Depends(),
    ):
    """Delete given survey including all its submissions and other data."""
    await survey_manager.delete(data.username, data.survey_name)


@app.post(**docs.SPECIFICATIONS['create_submission'])
async def create_submission(
        data: validation.CreateSubmissionRequestData = fastapi.Depends(),
    ):
    """Validate submission and store it under pending submissions."""
    survey = await survey_manager.fetch(
        data.username,
        data.survey_name,
        return_drafts=False,
    )
    survey.Submission(**data.submission)
    return await survey.submit(data.submission)


@app.get(**docs.SPECIFICATIONS['verify_submission'])
async def verify_submission(
        data: validation.VerifySubmissionRequestData = fastapi.Depends(),
    ):
    """Verify user token and either fail or redirect to success page."""
    survey = await survey_manager.fetch(
        data.username,
        data.survey_name,
        return_drafts=False,
    )
    return await survey.verify(data.verification_token)


@app.get(**docs.SPECIFICATIONS['fetch_results'])
@auth.authorize
async def fetch_results(
        data: validation.FetchResultsRequestData = fastapi.Depends(),
    ):
    """Fetch the results of the given survey."""
    survey = await survey_manager.fetch(data.username, data.survey_name)
    return await survey.aggregate()


@app.post(**docs.SPECIFICATIONS['generate_access_token'])
async def generate_access_token(
        data: validation.GenerateAccessTokenRequestData = fastapi.Depends(),
    ):
    """Generate a JWT access token containing the user's username."""
    return await account_manager.authenticate(
        data.authentication_credentials.identifier,
        data.authentication_credentials.password,
    )


@app.post(**docs.SPECIFICATIONS['verify_email_address'])
async def verify_email_address(
        data: validation.VerifyEmailAddressRequestData = fastapi.Depends(),
    ):
    """Verify an email address given the verification token sent via email."""
    return await account_manager.verify(
        data.verification_credentials.verification_token,
    )
