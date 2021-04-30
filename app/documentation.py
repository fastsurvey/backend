import pydantic
import fastapi as api
import fastapi.security


class ExceptionResponse(pydantic.BaseModel):
    detail: str


survey = {
    'configuration': {
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
    },
    'submission': {
        '1': True,
    },
    'results': {
        'count': 1,
        '1': 1,
    },
}

arguments = {
    'username': api.Path(
        ...,
        description='The name of the user',
        example='fastsurvey',
    ),
    'access_token': api.Depends(
        api.security.OAuth2PasswordBearer('/authentication')
    ),
    'survey_name': api.Path(
        ...,
        description='The name of the survey',
        example='hello-world',
    ),
    'configuration': api.Body(
        ...,
        description='The new configuration',
        example=survey['configuration'],
    ),
    'account_data': api.Body(
        ...,
        description='The updated account data',
        example={
            'username': 'fastsurvey',
            'email_address': 'support@fastsurvey.de',
            'password': '12345678'
        },
    ),
    'skip': api.Query(
        0,
        description='The index of the first returned configuration',
        example=0,
    ),
    'limit': api.Query(
        10,
        description='The query result count limit; 0 means no limit',
        example=10,
    ),
    'verification_token': api.Path(
        ...,
        description='The verification token',
        example='cb1d934026e78f083023e6daed5c7751c246467f01f6258029359c459b5edce07d16b45af13e05639c963d6d0662e63298fa68a01f03b5206e0aeb43daddef26',
    ),
    'submission': api.Body(
        ...,
        description='The user submission',
        example=survey['submission'],
    ),
    'authentication_credentials': api.Body(
        ...,
        description='The username or email address with the password',
        example={
            'identifier': 'fastsurvey',
            'password': '12345678'
        },
    ),
    'verification_credentials': api.Body(
        ...,
        description='The verification token together with the password',
        example={
            'verification_token': 'cb1d934026e78f083023e6daed5c7751c246467f01f6258029359c459b5edce07d16b45af13e05639c963d6d0662e63298fa68a01f03b5206e0aeb43daddef26',
            'password': '12345678'
        },
    ),
}

specifications = {
    'fetch_user': {
        'path': '/users/{username}',
        'responses': {
            200: {
                'content': {
                    'application/json': {
                        'example': {
                            'email_address': 'support@fastsurvey.de',
                            'creation_time': 1618530873,
                            'verified': True,
                        },
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
            404: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'user not found',
                        },
                    },
                },
            },
        },
    },
    'create_user': {
        'path': '/users/{username}',
        'responses': {
            400: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'examples': {
                            'invalid account data': {
                                'value': {
                                    'detail': 'invalid account data',
                                },
                            },
                            'username already taken': {
                                'value': {
                                    'detail': 'username already taken',
                                },
                            },
                            'email address already taken': {
                                'value': {
                                    'detail': 'email address already taken',
                                },
                            },
                        },
                    },
                },
            },
        },
    },
    'update_user': {
        'path': '/users/{username}',
        'responses': {
            400: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid account data',
                        },
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
            404: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'user not found',
                        },
                    },
                },
            },
        },
    },
    'delete_user': {
        'path': '/users/{username}',
        'responses': {
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
        },
    },
    'fetch_surveys': {
        'path': '/users/{username}/surveys',
        'responses': {
            200: {
                'content': {
                    'application/json': {
                        'example': [survey['configuration']],
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
        },
    },
    'fetch_survey': {
        'path': '/users/{username}/surveys/{survey_name}',
        'responses': {
            200: {
                'content': {
                    'application/json': {
                        'example': survey['configuration'],
                    },
                },
            },
            404: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'survey not found',
                        },
                    },
                },
            },
        },
    },
    'create_survey': {
        'path': '/users/{username}/surveys/{survey_name}',
        'responses': {
            400: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'examples': {
                            'invalid configuration': {
                                'value': {
                                    'detail': 'invalid configuration',
                                },
                            },
                            'survey exists': {
                                'value': {
                                    'detail': 'survey exists',
                                },
                            },
                        },
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
        },
    },
    'update_survey': {
        'path': '/users/{username}/surveys/{survey_name}',
        'responses': {
            400: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'examples': {
                            'invalid configuration': {
                                'value': {
                                    'detail': 'invalid configuration',
                                },
                            },
                            'not an existing survey': {
                                'value': {
                                    'detail': 'not an existing survey',
                                },
                            },
                        },
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
        },
    },
    'delete_survey': {
        'path': '/users/{username}/surveys/{survey_name}',
        'responses': {
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
        },
    },
    'create_submission': {
        'path': '/users/{username}/surveys/{survey_name}/submissions',
        'responses': {
            400: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'examples': {
                            'survey is not open yet': {
                                'value': {
                                    'detail': 'survey is not open yet',
                                },
                            },
                            'survey is closed': {
                                'value': {
                                    'detail': 'survey is closed',
                                },
                            },
                            'invalid submission': {
                                'value': {
                                    'detail': 'invalid submission',
                                },
                            },
                        },
                    },
                },
            },
            404: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'survey not found',
                        },
                    },
                },
            },
        },
    },
    'reset_survey': {
        'path': '/users/{username}/surveys/{survey_name}/submissions',
        'responses': {
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
        },
    },
    'verify_submission': {
        'path': '/users/{username}/surveys/{survey_name}/verification/{token}',
        'responses': {
            400: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'examples': {
                            'survey is not of type email': {
                                'value': {
                                    'detail': 'survey is not of type email',
                                },
                            },
                            'survey is not open yet': {
                                'value': {
                                    'detail': 'survey is not open yet',
                                },
                            },
                            'survey is closed': {
                                'value': {
                                    'detail': 'survey is closed',
                                },
                            },
                        },
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid verification token',
                        },
                    },
                },
            },
            404: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'survey not found',
                        },
                    },
                },
            },
        },
    },
    'fetch_results': {
        'path': '/users/{username}/surveys/{survey_name}/results',
        'responses': {
            200: {
                'content': {
                    'application/json': {
                        'example': survey['results'],
                    },
                },
            },
            400: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'survey is not yet closed',
                        },
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
            404: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'survey not found',
                        },
                    },
                },
            },
        },
    },
    'decode_access_token': {
        'path': '/authentication',
        'responses': {
            200: {
                'content': {
                    'application/json': {
                        'example': 'fastsurvey',
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid access token',
                        },
                    },
                },
            },
        },
    },
    'generate_access_token': {
        'path': '/authentication',
        'responses': {
            200: {
                'content': {
                    'application/json': {
                        'example': {
                            'access_token': b'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJGYXN0U3VydmV5Iiwic3ViIjoiYXBwbGUiLCJpYXQiOjE2MTYzNTA5NjAsImV4cCI6MTYxNjM1ODE2MH0.Vl8ndfMgE-LKcH5GOZZ_JEn2rL87Mg9wpihTvo-Cfukqr3vBI6I49EP109B2ZnEASnoXSzDRQSM438Pxxpm6aFMGSaxCJvVbPN3YhxKDKWel-3t7cslF5iwE8AlsYHQV6_6JZv-bZolUmScnGjXKEUBWn3x72AeFBm5I4O4VRWDt96umGfgtaPkBvXwW0eDIbGDIXR-MQF0vjiGnEd0GYwexgCj0uO80QTlN2oIH1kFtb612oqWJ3_Ipb2Ui6jwo0wVZW_I7zi5rKGrELsdGManwt7wUgp-V4779XXZ33IuojgS6kO45-aAkppBycv3cDqQdR_yjoRy6sZ4nryHEPzYKPtumtuY28Va2d9RpSxVHo1DkiyXmlrVWnmzyOuFVUxAMmblwaslc0es4igWtX_bZ141Vb6Vj96xk6pR6Wq9jjEhw9RsfyIVr2TwplzZZayVDl_9Pou3b8cZGRlotAYgWlYj9h0ZiI7hUvvXD24sFykx_HV3-hBPJJDmW3jwPRvRUtZEMic-1jAy-gMJs-irmeVOW6_Mh8LLncTRfutwJI4k6TqnPguX3LKEWu3uyGKT5zT2ZXanaTmBRVuFbON7-xb6ZvncdI5ttALixff2O67gXUjM7E9OrbauVWN6xqQ4-Wv70VJvtJa1MEvZOtC-JGwaF6C2WFNYKbnvB6hY',
                            'token_type': 'bearer',
                        },
                    },
                },
            },
            400: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'account not verified',
                        },
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'invalid password',
                        },
                    },
                },
            },
            404: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'user not found',
                        },
                    },
                },
            },
        },
    },
    'verify_email_address': {
        'path': '/verification',
        'responses': {
            200: {
                'content': {
                    'application/json': {
                        'example': {
                            'access_token': b'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJGYXN0U3VydmV5Iiwic3ViIjoiYXBwbGUiLCJpYXQiOjE2MTYzNTA5NjAsImV4cCI6MTYxNjM1ODE2MH0.Vl8ndfMgE-LKcH5GOZZ_JEn2rL87Mg9wpihTvo-Cfukqr3vBI6I49EP109B2ZnEASnoXSzDRQSM438Pxxpm6aFMGSaxCJvVbPN3YhxKDKWel-3t7cslF5iwE8AlsYHQV6_6JZv-bZolUmScnGjXKEUBWn3x72AeFBm5I4O4VRWDt96umGfgtaPkBvXwW0eDIbGDIXR-MQF0vjiGnEd0GYwexgCj0uO80QTlN2oIH1kFtb612oqWJ3_Ipb2Ui6jwo0wVZW_I7zi5rKGrELsdGManwt7wUgp-V4779XXZ33IuojgS6kO45-aAkppBycv3cDqQdR_yjoRy6sZ4nryHEPzYKPtumtuY28Va2d9RpSxVHo1DkiyXmlrVWnmzyOuFVUxAMmblwaslc0es4igWtX_bZ141Vb6Vj96xk6pR6Wq9jjEhw9RsfyIVr2TwplzZZayVDl_9Pou3b8cZGRlotAYgWlYj9h0ZiI7hUvvXD24sFykx_HV3-hBPJJDmW3jwPRvRUtZEMic-1jAy-gMJs-irmeVOW6_Mh8LLncTRfutwJI4k6TqnPguX3LKEWu3uyGKT5zT2ZXanaTmBRVuFbON7-xb6ZvncdI5ttALixff2O67gXUjM7E9OrbauVWN6xqQ4-Wv70VJvtJa1MEvZOtC-JGwaF6C2WFNYKbnvB6hY',
                            'token_type': 'bearer',
                        },
                    },
                },
            },
            400: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'example': {
                            'detail': 'account already verified',
                        },
                    },
                },
            },
            401: {
                'model': ExceptionResponse,
                'content': {
                    'application/json': {
                        'examples': {
                            'invalid token': {
                                'value': {
                                    'detail': 'invalid verification token',
                                },
                            },
                            'invalid password': {
                                'value': {
                                    'detail': 'invalid password',
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}
