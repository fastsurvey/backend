import pydantic

import app.documentation as docs
import app.models as models


class ReadUserRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]


class CreateUserRequest(models.BaseModel):
    account_data: models.AccountData = docs.ARGUMENTS["account_data"]


class UpdateUserRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]
    account_data: models.AccountDataUpdate = docs.ARGUMENTS["account_data"]


class DeleteUserRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]


class ReadSurveysRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]


class ReadSurveyRequest(models.BaseModel):
    username: models.Username = docs.ARGUMENTS["username"]
    survey_name: models.Username = docs.ARGUMENTS["survey_name"]


class CreateSurveyRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]
    configuration: models.Configuration = docs.ARGUMENTS["configuration"]


class UpdateSurveyRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]
    survey_name: models.SurveyName = docs.ARGUMENTS["survey_name"]
    configuration: models.Configuration = docs.ARGUMENTS["configuration"]


class DeleteSurveyRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]
    survey_name: models.SurveyName = docs.ARGUMENTS["survey_name"]


class ReadSubmissionsRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]
    survey_name: models.SurveyName = docs.ARGUMENTS["survey_name"]


class CreateSubmissionRequest(models.BaseModel):
    username: models.Username = docs.ARGUMENTS["username"]
    survey_name: models.SurveyName = docs.ARGUMENTS["survey_name"]
    submission: dict = docs.ARGUMENTS["submission"]


class ResetSurveyRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]
    survey_name: models.SurveyName = docs.ARGUMENTS["survey_name"]


class VerifySubmissionRequest(models.BaseModel):
    username: models.Username = docs.ARGUMENTS["username"]
    survey_name: models.SurveyName = docs.ARGUMENTS["survey_name"]
    verification_credentials: models.VerificationCredentials = docs.ARGUMENTS[
        "verification_credentials"
    ]


class ReadResultsRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]
    username: models.Username = docs.ARGUMENTS["username"]
    survey_name: models.SurveyName = docs.ARGUMENTS["survey_name"]


class CreateAccessTokenRequest(models.BaseModel):
    authentication_credentials: models.AuthenticationCredentials = docs.ARGUMENTS[
        "authentication_credentials"
    ]


class VerifyAccessTokenRequest(models.BaseModel):
    verification_credentials: models.VerificationCredentials = docs.ARGUMENTS[
        "verification_credentials"
    ]


class DeleteAccessTokenRequest(models.BaseModel):
    access_token: models.Token = docs.ARGUMENTS["access_token"]


class VerifyAccountEmailAddressRequest(models.BaseModel):
    verification_credentials: models.VerificationCredentials = docs.ARGUMENTS[
        "verification_credentials"
    ]
