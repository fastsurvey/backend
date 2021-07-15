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
    '1': 1,
}


ARGUMENTS = {
    'username': fastapi.Path(
        ...,
        description='The name of the user',
        example='fastsurvey',
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
            'username': 'fastsurvey',
            'email_address': 'support@fastsurvey.de',
            'password': '12345678'
        },
    ),
    'skip': fastapi.Query(
        0,
        description='The index of the first returned configuration',
        example=0,
    ),
    'limit': fastapi.Query(
        10,
        description='The query result count limit; 0 means no limit',
        example=10,
    ),
    'verification_token': fastapi.Path(
        ...,
        description='The verification token',
        example='cb1d934026e78f083023e6daed5c7751c246467f01f6258029359c459b5edce07d16b45af13e05639c963d6d0662e63298fa68a01f03b5206e0aeb43daddef26',
    ),
    'submission': fastapi.Body(
        ...,
        description='The user submission',
        example=_SAMPLE_SUBMISSION,
    ),
    'authentication_credentials': fastapi.Body(
        ...,
        description='The username or email address with the password',
        example={
            'identifier': 'fastsurvey',
            'password': '12345678'
        },
    ),
    'verification_credentials': fastapi.Body(
        ...,
        description='The verification token together with the password',
        example={
            'verification_token': 'cb1d934026e78f083023e6daed5c7751c246467f01f6258029359c459b5edce07d16b45af13e05639c963d6d0662e63298fa68a01f03b5206e0aeb43daddef26',
            'password': '12345678'
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
            'commit_sha': '219170f284f2d5e959d70689043aa0747cc52fc1',
            'branch_name': 'master',
            'start_time': 1623779418,
        },
    ),
    'fetch_user': _generate_responses_documentation(
        path='/users/{username}',
        response={
            'email_address': 'support@fastsurvey.de',
            'creation_time': 1618530873,
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
            errors.InvalidAccountDataError,
            errors.UsernameAlreadyTakenError,
            errors.EmailAddressAlreadyTakenError,
        ],
    ),
    'update_user': _generate_responses_documentation(
        path='/users/{username}',
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.InvalidAccountDataError,
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
    'fetch_surveys': _generate_responses_documentation(
        path='/users/{username}/surveys',
        response=[_SAMPLE_CONFIGURATION],
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    'fetch_survey': _generate_responses_documentation(
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
            errors.InvalidConfigurationError,
            errors.SurveyNameAlreadyTakenError,
        ],
    ),
    'update_survey': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}',
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.InvalidConfigurationError,
            errors.SurveyNameAlreadyTakenError,
            errors.SurveyNotFoundError,
        ],
    ),
    'delete_survey': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}',
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    'create_submission': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}/submissions',
        error_classes=[
            errors.InvalidTimingError,
            errors.InvalidSubmissionError,
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
    'fetch_results': _generate_responses_documentation(
        path='/users/{username}/surveys/{survey_name}/results',
        response=_SAMPLE_RESULTS,
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
            errors.SurveyNotFoundError,
        ],
    ),
    'decode_access_token': _generate_responses_documentation(
        path='/authentication',
        response='fastsurvey',
        error_classes=[
            errors.InvalidAccessTokenError,
        ],
    ),
    'generate_access_token': _generate_responses_documentation(
        path='/authentication',
        response={
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJGYXN0U3VydmV5Iiwic3ViIjoiYXBwbGUiLCJpYXQiOjE2MTYzNTA5NjAsImV4cCI6MTYxNjM1ODE2MH0.Vl8ndfMgE-LKcH5GOZZ_JEn2rL87Mg9wpihTvo-Cfukqr3vBI6I49EP109B2ZnEASnoXSzDRQSM438Pxxpm6aFMGSaxCJvVbPN3YhxKDKWel-3t7cslF5iwE8AlsYHQV6_6JZv-bZolUmScnGjXKEUBWn3x72AeFBm5I4O4VRWDt96umGfgtaPkBvXwW0eDIbGDIXR-MQF0vjiGnEd0GYwexgCj0uO80QTlN2oIH1kFtb612oqWJ3_Ipb2Ui6jwo0wVZW_I7zi5rKGrELsdGManwt7wUgp-V4779XXZ33IuojgS6kO45-aAkppBycv3cDqQdR_yjoRy6sZ4nryHEPzYKPtumtuY28Va2d9RpSxVHo1DkiyXmlrVWnmzyOuFVUxAMmblwaslc0es4igWtX_bZ141Vb6Vj96xk6pR6Wq9jjEhw9RsfyIVr2TwplzZZayVDl_9Pou3b8cZGRlotAYgWlYj9h0ZiI7hUvvXD24sFykx_HV3-hBPJJDmW3jwPRvRUtZEMic-1jAy-gMJs-irmeVOW6_Mh8LLncTRfutwJI4k6TqnPguX3LKEWu3uyGKT5zT2ZXanaTmBRVuFbON7-xb6ZvncdI5ttALixff2O67gXUjM7E9OrbauVWN6xqQ4-Wv70VJvtJa1MEvZOtC-JGwaF6C2WFNYKbnvB6hY',
            'token_type': 'bearer',
        },
        error_classes=[
            errors.InvalidPasswordError,
            errors.AccountNotVerifiedError,
            errors.UserNotFoundError,
        ],
    ),
    'refresh_access_token': _generate_responses_documentation(
        path='/authentication',
        response={
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJGYXN0U3VydmV5Iiwic3ViIjoiYXBwbGUiLCJpYXQiOjE2MTYzNTA5NjAsImV4cCI6MTYxNjM1ODE2MH0.Vl8ndfMgE-LKcH5GOZZ_JEn2rL87Mg9wpihTvo-Cfukqr3vBI6I49EP109B2ZnEASnoXSzDRQSM438Pxxpm6aFMGSaxCJvVbPN3YhxKDKWel-3t7cslF5iwE8AlsYHQV6_6JZv-bZolUmScnGjXKEUBWn3x72AeFBm5I4O4VRWDt96umGfgtaPkBvXwW0eDIbGDIXR-MQF0vjiGnEd0GYwexgCj0uO80QTlN2oIH1kFtb612oqWJ3_Ipb2Ui6jwo0wVZW_I7zi5rKGrELsdGManwt7wUgp-V4779XXZ33IuojgS6kO45-aAkppBycv3cDqQdR_yjoRy6sZ4nryHEPzYKPtumtuY28Va2d9RpSxVHo1DkiyXmlrVWnmzyOuFVUxAMmblwaslc0es4igWtX_bZ141Vb6Vj96xk6pR6Wq9jjEhw9RsfyIVr2TwplzZZayVDl_9Pou3b8cZGRlotAYgWlYj9h0ZiI7hUvvXD24sFykx_HV3-hBPJJDmW3jwPRvRUtZEMic-1jAy-gMJs-irmeVOW6_Mh8LLncTRfutwJI4k6TqnPguX3LKEWu3uyGKT5zT2ZXanaTmBRVuFbON7-xb6ZvncdI5ttALixff2O67gXUjM7E9OrbauVWN6xqQ4-Wv70VJvtJa1MEvZOtC-JGwaF6C2WFNYKbnvB6hY',
            'token_type': 'bearer',
        },
        error_classes=[
            errors.InvalidAccessTokenError,
            errors.AccessForbiddenError,
        ],
    ),
    'verify_email_address': _generate_responses_documentation(
        path='/verification',
        response={
            'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJGYXN0U3VydmV5Iiwic3ViIjoiYXBwbGUiLCJpYXQiOjE2MTYzNTA5NjAsImV4cCI6MTYxNjM1ODE2MH0.Vl8ndfMgE-LKcH5GOZZ_JEn2rL87Mg9wpihTvo-Cfukqr3vBI6I49EP109B2ZnEASnoXSzDRQSM438Pxxpm6aFMGSaxCJvVbPN3YhxKDKWel-3t7cslF5iwE8AlsYHQV6_6JZv-bZolUmScnGjXKEUBWn3x72AeFBm5I4O4VRWDt96umGfgtaPkBvXwW0eDIbGDIXR-MQF0vjiGnEd0GYwexgCj0uO80QTlN2oIH1kFtb612oqWJ3_Ipb2Ui6jwo0wVZW_I7zi5rKGrELsdGManwt7wUgp-V4779XXZ33IuojgS6kO45-aAkppBycv3cDqQdR_yjoRy6sZ4nryHEPzYKPtumtuY28Va2d9RpSxVHo1DkiyXmlrVWnmzyOuFVUxAMmblwaslc0es4igWtX_bZ141Vb6Vj96xk6pR6Wq9jjEhw9RsfyIVr2TwplzZZayVDl_9Pou3b8cZGRlotAYgWlYj9h0ZiI7hUvvXD24sFykx_HV3-hBPJJDmW3jwPRvRUtZEMic-1jAy-gMJs-irmeVOW6_Mh8LLncTRfutwJI4k6TqnPguX3LKEWu3uyGKT5zT2ZXanaTmBRVuFbON7-xb6ZvncdI5ttALixff2O67gXUjM7E9OrbauVWN6xqQ4-Wv70VJvtJa1MEvZOtC-JGwaF6C2WFNYKbnvB6hY',
            'token_type': 'bearer',
        },
        error_classes=[
            errors.InvalidVerificationTokenError,
            errors.InvalidPasswordError,
        ],
    ),
}
