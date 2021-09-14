import pydantic
import fastapi

import app.errors as errors


_SAMPLE_SURVEY_NAME = 'option'

_SAMPLE_CONFIGURATION = {
    'survey_name': 'option',
    'title': 'Option Test',
    'description': '',
    'start': 1000000000,
    'end': 2000000000,
    'draft': False,
    'authentication': 'open',
    'limit': 0,
    'fields': [
        {
            'type': 'option',
            'title': 'I have read and agree to the terms and conditions',
            'description': '',
            'required': True
        }
    ],
}

_SAMPLE_SUBMISSION = {
    '1': True,
},

_SAMPLE_RESULTS = {
    'count': 1,
    'aggregation': [
        1,
    ],
}


ARGUMENTS = {
    'username': fastapi.Path(
        ...,
        description='The name of the user',
        example='blueberry',
    ),
    'access_token': fastapi.Depends(
        fastapi.security.OAuth2PasswordBearer('/authentication')
    ),
    'survey_name': fastapi.Path(
        ...,
        description='The name of the survey',
        example=_SAMPLE_SURVEY_NAME,
    ),
    'configuration': fastapi.Body(
        ...,
        description='The survey configuration',
        example=_SAMPLE_CONFIGURATION,
    ),
    'account_data': fastapi.Body(
        ...,
        description='The account data',
        example={
            'username': 'blueberry',
            'email_address': 'contact@fastsurvey.de',
            'password': '12345678'
        },
    ),
    'verification_token': fastapi.Path(
        ...,
        description='The verification token',
        example='6Ca1j7b5P3D8fO6WpsUHsE_eN3Fqq8V_sp_sV4RB2ubw9mtwRUM2cQh26jS_r65v',
    ),
    'submission': fastapi.Body(
        ...,
        description='The user submission',
        example=_SAMPLE_SUBMISSION,
    ),
    'authentication_credentials': fastapi.Body(
        ...,
        description='The username or email address together with the password',
        example={
            'identifier': 'blueberry',
            'password': '12345678'
        },
    ),
    'verification_credentials': fastapi.Body(
        ...,
        description='The verification token',
        example={
            'verification_token': '6Ca1j7b5P3D8fO6WpsUHsE_eN3Fqq8V_sp_sV4RB2ubw9mtwRUM2cQh26jS_r65v',
        },
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
            'model': ErrorResponse,
            'content': {
                'application/json': {
                    'examples' if multiple else 'example': {},
                },
            },
        }
        out.setdefault(status, template)
        if multiple:
            examples = out[status]['content']['application/json']['examples']
            examples[error_class.DETAIL] = {'value': {
                'detail': error_class.DETAIL,
            }}
        else:
            out[status]['content']['application/json']['example'] = {
                'detail': error_class.DETAIL,
            }
    return out


def _generate_responses_documentation(path, response=None, error_classes=[]):
    responses = {}
    if response:
        responses[200] = {
            'content': {
                'application/json': {
                    'example': response,
                }
            },
        }
    responses.update(_generate_error_documentation(error_classes))
    return {'path': path, 'responses': responses}


SPECIFICATIONS = {
    'server_status': _generate_responses_documentation(
        path='/status',
        response={
            'environment': 'production',
            'commit_sha': '219170f284f2d5e959d70689043aa0747cc52fc1',
            'branch_name': 'master',
            'start_time': 1623779418,
        },
    ),
    'read_user': _generate_responses_documentation(
        path='/users/{username}',
        response={
            'email_address': 'contact@fastsurvey.de',
            'verified': True,
        },
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.UserNotFoundError,
        ],
    ),
    'create_user': _generate_responses_documentation(
        path='/users/{username}',
        error_classes=[
            errors.UsernameAlreadyTakenError,
            errors.EmailAddressAlreadyTakenError,
        ],
    ),
    'update_user': _generate_responses_documentation(
        path='/users/{username}',
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.UserNotFoundError,
        ],
    ),
    'delete_user': _generate_responses_documentation(
        path='/users/{username}',
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    'read_surveys': _generate_responses_documentation(
        path='/users/{username}/surveys',
        response=[_SAMPLE_CONFIGURATION],
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    'read_survey': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}',
        response=_SAMPLE_CONFIGURATION,
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNotFoundError,
        ],
    ),
    'create_survey': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}',
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNameAlreadyTakenError,
        ],
    ),
    'update_survey': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}',
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNameAlreadyTakenError,
            errors.SurveyNotFoundError,
            errors.SubmissionsExistError,
        ],
    ),
    'delete_survey': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}',
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    'read_submissions': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}/submissions',
        response=[_SAMPLE_SUBMISSION],
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNotFoundError,
        ],
    ),
    'create_submission': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}/submissions',
        error_classes=[
            errors.InvalidTimingError,
            errors.SurveyNotFoundError,
        ],
    ),
    'reset_survey': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}/submissions',
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    'verify_submission': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}/verification/{verification_token}',
        error_classes=[
            errors.InvalidVerificationTokenError,
            errors.SurveyNotFoundError,
            errors.InvalidTimingError,
        ],
    ),
    'read_results': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}/results',
        response=_SAMPLE_RESULTS,
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNotFoundError,
        ],
    ),
    'login': _generate_responses_documentation(
        path='/authentication',
        response={
            'username': 'blueberry',
            'access_token': '6Ca1j7b5P3D8fO6WpsUHsE_eN3Fqq8V_sp_sV4RB2ubw9mtwRUM2cQh26jS_r65v',
        },
        error_classes=[
            errors.InvalidPasswordError,
            errors.AccountNotVerifiedError,
            errors.UserNotFoundError,
        ],
    ),
    'logout': _generate_responses_documentation(
        path='/authentication',
        error_classes=[
            errors.InvalidAccessTokenError,
        ],
    ),
    'verify_account_email_address': _generate_responses_documentation(
        path='/verification',
        error_classes=[
            errors.InvalidVerificationTokenError,
        ],
    ),
}
