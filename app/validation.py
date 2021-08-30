import pydantic

import app.documentation as docs
import app.models as models


class FetchUserRequestData(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS['access_token']
    username: models.Username = docs.ARGUMENTS['username']


class CreateUserRequestData(models.BaseModel):
    username: models.Username = docs.ARGUMENTS['username']
    account_data: models.AccountData = docs.ARGUMENTS['account_data']

    @pydantic.validator('account_data')
    def validate_account_data(cls, v, values):
        if 'username' in values and v.username != values['username']:
            raise ValueError('usernames in route and body must be equal')
        return v


class UpdateUserRequestData(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS['access_token']
    username: models.Username = docs.ARGUMENTS['username']
    account_data: models.AccountData = docs.ARGUMENTS['account_data']


class DeleteUserRequestData(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS['access_token']
    username: models.Username = docs.ARGUMENTS['username']


class FetchSurveysRequestData(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS['access_token']
    username: models.Username = docs.ARGUMENTS['username']
    skip: pydantic.conint(strict=True, ge=0) = docs.ARGUMENTS['skip']
    limit: pydantic.conint(strict=True, ge=0) = docs.ARGUMENTS['limit']


class FetchSurveyRequestData(models.BaseModel):
    username: models.Username = docs.ARGUMENTS['username']
    survey_name: models.Username = docs.ARGUMENTS['survey_name']


class CreateSurveyRequestData(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS['access_token']
    username: models.Username = docs.ARGUMENTS['username']
    survey_name: models.SurveyName = docs.ARGUMENTS['survey_name']
    configuration: models.Configuration = docs.ARGUMENTS['configuration']

    @pydantic.validator('configuration')
    def validate_configuration(cls, v, values):
        if 'survey_name' in values and v.survey_name!= values['survey_name']:
            raise ValueError('survey names in route and body must be equal')
        return v


class UpdateSurveyRequestData(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS['access_token']
    username: models.Username = docs.ARGUMENTS['username']
    survey_name: models.SurveyName = docs.ARGUMENTS['survey_name']
    configuration: models.Configuration = docs.ARGUMENTS['configuration']


class ResetSurveyRequestData(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS['access_token']
    username: models.Username = docs.ARGUMENTS['username']
    survey_name: models.SurveyName = docs.ARGUMENTS['survey_name']


class DeleteSurveyRequestData(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS['access_token']
    username: models.Username = docs.ARGUMENTS['username']
    survey_name: models.SurveyName = docs.ARGUMENTS['survey_name']


class CreateSubmissionRequestData(models.BaseModel):
    username: models.Username = docs.ARGUMENTS['username']
    survey_name: models.SurveyName = docs.ARGUMENTS['survey_name']
    submission: dict = docs.ARGUMENTS['submission']


class VerifySubmissionRequestData(models.BaseModel):
    username: models.Username = docs.ARGUMENTS['username']
    survey_name: models.SurveyName = docs.ARGUMENTS['survey_name']
    verification_token: models.Token = docs.ARGUMENTS['verification_token']


class FetchResultsRequestData(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS['access_token']
    username: models.Username = docs.ARGUMENTS['username']
    survey_name: models.SurveyName = docs.ARGUMENTS['survey_name']


class GenerateAccessTokenRequestData(models.BaseModel):
    authentication_credentials: models.AuthenticationCredentials = (
        docs.ARGUMENTS['authentication_credentials']
    )


class VerifyEmailAddressRequestData(models.BaseModel):
    verification_credentials: models.VerificationCredentials = (
        docs.ARGUMENTS['verification_credentials']
    )
