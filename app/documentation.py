import fastapi
import pydantic

import app.errors as errors


_SAMPLE_SURVEY_NAME = "simple"

_SAMPLE_CONFIGURATION = {
    "survey_name": "simple",
    "title": "Simple Test Survey",
    "description": "",
    "start": 0,
    "end": 4102444800,
    "draft": False,
    "fields": [
        {
            "identifier": 0,
            "type": "selection",
            "title": "What is your favorite fruit?",
            "description": "",
            "options": ["Asparagus", "Spinach", "Artichoke"],
            "min_select": 1,
            "max_select": 1,
        }
    ],
}

_SAMPLE_SUBMISSION = (
    {
        "0": ["Asparagus"],
    },
)

_SAMPLE_RESULTS = {
    "count": 1,
    "1": {"count": 1, "value": {"Asparagus": 1, "Spinach": 0, "Artichoke": 0}},
}


ARGUMENTS = {
    "username": fastapi.Path(
        ...,
        description="The name of the user",
        example="blueberry",
    ),
    "access_token": fastapi.Depends(
        fastapi.security.OAuth2PasswordBearer("/authentication")
    ),
    "survey_name": fastapi.Path(
        ...,
        description="The name of the survey",
        example=_SAMPLE_SURVEY_NAME,
    ),
    "configuration": fastapi.Body(
        ...,
        description="The survey configuration",
        example=_SAMPLE_CONFIGURATION,
    ),
    "account_data": fastapi.Body(
        ...,
        description="The account data",
        example={
            "username": "blueberry",
            "email_address": "contact@fastsurvey.de",
            "password": "12345678",
        },
    ),
    "submission": fastapi.Body(
        ...,
        description="The user submission",
        example=_SAMPLE_SUBMISSION,
    ),
    "authentication_credentials": fastapi.Body(
        ...,
        description="The username or email address together with the password",
        example={"identifier": "blueberry", "password": "12345678"},
    ),
    "verification_credentials": fastapi.Body(
        ...,
        description="The verification token",
        example={
            "verification_token": (
                "6Ca1j7b5P3D8fO6WpsUHsE_eN3Fqq8V_sp_sV4RB2ubw9mtwRUM2cQh26jS_r65v"
            ),
        },
    ),
    "skip": fastapi.Query(
        0,
        description="The index of the first submission",
        example=0,
    ),
    "limit": fastapi.Query(
        0,
        description="The query result count limit; 0 means no limit",
        example=0,
    ),
}


class ErrorResponse(pydantic.BaseModel):
    detail: str


def _generate_error_documentation(error_classes):
    """Generate the OpenAPI error specifications for given route errors."""
    out = dict()
    status_codes = [error_class.STATUS_CODE for error_class in error_classes]
    for status, error_class in zip(status_codes, error_classes):
        multiple = status_codes.count(error_class.STATUS_CODE) > 1
        template = {
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples" if multiple else "example": {},
                },
            },
        }
        out.setdefault(status, template)
        if multiple:
            examples = out[status]["content"]["application/json"]["examples"]
            examples[error_class.DETAIL] = {
                "value": {
                    "detail": error_class.DETAIL,
                }
            }
        else:
            out[status]["content"]["application/json"]["example"] = {
                "detail": error_class.DETAIL,
            }
    return out


def _generate_responses_documentation(path, response=None, error_classes=[]):
    responses = {}
    if response:
        responses[200] = {
            "content": {
                "application/json": {
                    "example": response,
                }
            },
        }
    responses.update(_generate_error_documentation(error_classes))
    return {"path": path, "responses": responses}


SPECIFICATIONS = {
    "read_status": _generate_responses_documentation(
        path="/status",
        response={
            "environment": "production",
            "commit_sha": "219170f284f2d5e959d70689043aa0747cc52fc1",
            "branch_name": "master",
            "start_time": 1623779418,
        },
    ),
    "read_user": _generate_responses_documentation(
        path="/users/{username}",
        response={
            "email_address": "contact@fastsurvey.de",
            "verified": True,
        },
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.UserNotFoundError,
        ],
    ),
    "create_user": _generate_responses_documentation(
        path="/users",
        error_classes=[
            errors.UsernameAlreadyTakenError,
            errors.EmailAddressAlreadyTakenError,
        ],
    ),
    "update_user": _generate_responses_documentation(
        path="/users/{username}",
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.UserNotFoundError,
            errors.UsernameAlreadyTakenError,
            errors.EmailAddressAlreadyTakenError,
        ],
    ),
    "delete_user": _generate_responses_documentation(
        path="/users/{username}",
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    "read_surveys": _generate_responses_documentation(
        path="/users/{username}/surveys",
        response=[_SAMPLE_CONFIGURATION],
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    "read_survey": _generate_responses_documentation(
        path="/users/{username}/surveys/{survey_name}",
        response=_SAMPLE_CONFIGURATION,
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNotFoundError,
        ],
    ),
    "create_survey": _generate_responses_documentation(
        path="/users/{username}/surveys",
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNameAlreadyTakenError,
        ],
    ),
    "update_survey": _generate_responses_documentation(
        path="/users/{username}/surveys/{survey_name}",
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNameAlreadyTakenError,
            errors.SurveyNotFoundError,
        ],
    ),
    "delete_survey": _generate_responses_documentation(
        path="/users/{username}/surveys/{survey_name}",
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    "read_submissions": _generate_responses_documentation(
        path="/users/{username}/surveys/{survey_name}/submissions",
        response=[_SAMPLE_SUBMISSION],
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNotFoundError,
        ],
    ),
    "create_submission": _generate_responses_documentation(
        path="/users/{username}/surveys/{survey_name}/submissions",
        error_classes=[
            errors.InvalidTimingError,
            errors.SurveyNotFoundError,
        ],
    ),
    "reset_survey": _generate_responses_documentation(
        path="/users/{username}/surveys/{survey_name}/submissions",
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    "verify_submission": _generate_responses_documentation(
        path="/users/{username}/surveys/{survey_name}/verification",
        error_classes=[
            errors.InvalidVerificationTokenError,
            errors.SurveyNotFoundError,
            errors.InvalidTimingError,
        ],
    ),
    "read_results": _generate_responses_documentation(
        path="/users/{username}/surveys/{survey_name}/results",
        response=_SAMPLE_RESULTS,
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNotFoundError,
        ],
    ),
    "create_access_token": _generate_responses_documentation(
        path="/authentication",
        response={
            "username": "blueberry",
            "access_token": (
                "6Ca1j7b5P3D8fO6WpsUHsE_eN3Fqq8V_sp_sV4RB2ubw9mtwRUM2cQh26jS_r65v"
            ),
        },
        error_classes=[
            errors.InvalidPasswordError,
            errors.AccountNotVerifiedError,
            errors.UserNotFoundError,
        ],
    ),
    "verify_access_token": _generate_responses_documentation(
        path="/authentication",
        response={
            "username": "blueberry",
            "access_token": (
                "6Ca1j7b5P3D8fO6WpsUHsE_eN3Fqq8V_sp_sV4RB2ubw9mtwRUM2cQh26jS_r65v"
            ),
        },
        error_classes=[
            errors.InvalidVerificationTokenError,
        ],
    ),
    "delete_access_token": _generate_responses_documentation(
        path="/authentication",
        error_classes=[
            errors.InvalidAccessTokenError,
        ],
    ),
    "verify_account_email_address": _generate_responses_documentation(
        path="/verification",
        error_classes=[
            errors.InvalidVerificationTokenError,
        ],
    ),
}
