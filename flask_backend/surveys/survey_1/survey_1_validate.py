

from flask_backend.support_functions import formatting
from cerberus import Validator



def check_email(field, email_string, error):

    def invalid_format():
        error(field, 'format invalid')
        return

    def invalid_domain():
        error(field, 'only ...@mytum.de addresses allowed')
        return

    if type(email_string) == str:

        # Chained if statements because the latter depend on the previous
        # ones to be true in order not to throw an interpreter error

        email_parts = email_string.split('@')
        if len(email_parts) != 2:
            # not exactly one '@'
            return invalid_format()

        if len(email_parts[0]) == 0:
            # nothing before '@'
            return invalid_format()

        if '.' not in email_parts[1]:
            # no '.' after '@'
            return invalid_format()

        email_domain_parts = email_parts[1].split('.')
        if any([(len(part) == 0) for part in email_domain_parts]):
            # '..' after '@'
            return invalid_format()

        if email_parts[1] != "mytum.de":
            # only mytum.de is allowed to prevent people to submit stuff with
            # both of their @tum.de and @mytum.de addresses
            invalid_domain()


def check_election(field, election_dict, error):

    election_count = 0

    for name in ['albers', 'deniers', 'schmidt', 'ballweg']:
        election_count += 1 if election_dict[name] else 0

    if (election_count == 0):
        error(field, 'please select at least 1 candidate')

    if (election_count == 4):
        error(field, 'please select at most 3 candidates')


survey_1_schema = {
    'email': {
        'type': 'string',
        'required': True,
        'check_with': check_email,
    },
    'election': {
        'type': 'dict',
        'required': True,
        'schema': {
            'albers': {'type': 'boolean', 'required': True},
            'deniers': {'type': 'boolean', 'required': True},
            'schmidt': {'type': 'boolean', 'required': True},
            'ballweg': {'type': 'boolean', 'required': True},
        },
        'check_with': check_election,
    },
}


survey_1_validator = Validator(survey_1_schema)

def validate_survey_1(params_dict):
    if "form-data" not in params_dict:
        return formatting.status("form-data missing")

    if survey_1_validator.validate(params_dict["form-data"]):
        return formatting.status('ok')
    else:
        return formatting.status('validation error', errors=survey_1_validator.errors)


if __name__ == "__main__":

    example_1 = {
        'form-data': {
            'email': 'ge69zeh@mytu.de',
            'election': {
                'albers': True,
                'deniers': True,
                'schmidt': True,
                'ballweg': True,
            }
        }
    }

    example_2 = {
        'form-data': {
            'email': 'dd@mytum.d',
            'election': {
                'albers': True,
                'deniers': True,
                'schmidt': True,
                'ballweg': False,
            }
        }
    }

    example_3 = {
        'form-data': {
            'email': '@mytum.de',
            'election': {
                'albers': True,
                'deniers': True,
                'schmidt': False,
                'ballweg': False,
            }
        }
    }

    example_4 = {
        'form-data': {
            'email': 'ge69zeh@mytum.de',
            'election': {
                'albers': False,
                'deniers': False,
                'schmidt': False,
                'ballweg': False,
            }
        }
    }

    for example in [example_1, example_2, example_3, example_4]:
        print(validate_survey_1(example))
