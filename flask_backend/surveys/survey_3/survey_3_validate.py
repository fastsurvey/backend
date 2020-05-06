

from flask_backend.support_functions import formatting
from cerberus import Validator



def check_email(field, email_string, error):

    def invalid_format():
        error(field, 'format invalid')
        return

    if type(email_string) == str:

        if any(invalid_string in email_string for invalid_string in ["script", "<", ">"]):
            error(field, 'XSS alert')
            return

        # Chained if statements because the latter depend on the previous
        # ones to be true in order not to throw an interpreter error

        email_parts = email_string.split('@')
        if len(email_parts) != 2:
            # not exactly one '@'
            return invalid_format()

        if len(email_parts[0]) == 0:
            # nothing before '@'
            return invalid_format()

        if email_parts[1] != "mytum.de" or len(email_parts[0]) != 7:
            # only mytum.de is allowed to prevent people to submit stuff with
            # both of their @tum.de and @mytum.de addresses
            error(field, 'only <lrz-kennung>@mytum.de addresses allowed')
            return


def check_election(field, election_dict, error):
    election_count = 0

    for key in ['ja', 'nein', 'enthaltung']:
        election_count += 1 if election_dict[key] else 0

    if (election_count != 1):
        error(field, 'select at exactly 1 option')


survey_3_schema = {
    'email': {
        'type': 'string',
        'required': True,
        'check_with': check_email,
    },
    'election': {
        'type': 'dict',
        'required': True,
        'schema': {
            'ja': {'type': 'boolean', 'required': True},
            'nein': {'type': 'boolean', 'required': True},
            'enthaltung': {'type': 'boolean', 'required': True},
        },
        'check_with': check_election,
    },
}


survey_3_validator = Validator(survey_3_schema)

def validate(params_dict):
    if "form_data" not in params_dict:
        return formatting.status("form_data missing", status_code=500)

    if survey_3_validator.validate(params_dict["form_data"]):
        return formatting.status('ok')
    else:
        return formatting.status('validation error', errors=survey_3_validator.errors, status_code=400)
