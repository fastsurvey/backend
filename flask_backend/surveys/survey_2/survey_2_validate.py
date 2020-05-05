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


def check_election(field, election_dict, error, max_votes):
    election_count = 0

    for key in election_dict:
        if key != "andere":
            election_count += 1 if election_dict[key] else 0

    if (election_count > max_votes):
        error(field, f'select at most {max_votes} candidates')


def check_election_1(field, election_dict, error):
    check_election(field, election_dict, error, 1)


def check_election_2(field, election_dict, error):
    check_election(field, election_dict, error, 2)


survey_2_schema = {
    'email': {
        'type': 'string',
        'required': True,
        'check_with': check_email,
    },
    'election': {
        'type': 'dict',
        'required': True,
        'schema': {}
    }
}

for electee in [
    "erstsemester.koenigbaur", "erstsemester.wernsdorfer", "erstsemester.andere",
    "veranstaltungen.ritter", "veranstaltungen.pro", "veranstaltungen.andere",
    "skripte.lukasch", "skripte.limant", "skripte.andere",
    "quantum.albrecht", "quantum.roithmaier", "quantum.andere",
    "kooperationen.winckler", "kooperationen.andere",
    "it.kalk", "it.sittig", "it.andere",
    "evaluationen.reichelt", "evaluationen.andere",
    "hochschulpolitik.armbruster", "hochschulpolitik.paulus", "hochschulpolitik.andere",
    "finanzen.spicker", "finanzen.schuh", "finanzen.andere",
    "pr.werle", "pr.andere",
]:
    referat = electee.split('.')[0]
    name = electee.split('.')[1]

    if referat not in survey_2_schema["election"]["schema"]:
        survey_2_schema["election"]["schema"][referat] = {
            'type': 'dict',
            'required': True,
            'schema': {
                'andere': {'type': 'string', 'required': True},
            },
            'check_with': check_election_2,
        }

    if name != "andere":
        survey_2_schema["election"]["schema"][referat]["schema"][name] = {'type': 'boolean', 'required': True}

survey_2_validator = Validator(survey_2_schema)


def validate(params_dict):
    if "form_data" not in params_dict:
        return formatting.status("form_data missing", status_code=500)

    if survey_2_validator.validate(params_dict["form_data"]):
        return formatting.status('ok')
    else:
        return formatting.status('validation error', errors=survey_2_validator.errors, status_code=400)


if __name__ == "__main__":

    example_1 = {
        "form_data": {
            "email": "ge69zeh@mytum.de",
            "election": {
                "erstsemester": {
                    "koenigbaur": False,
                    "wernsdorfer": False,
                    "andere": ""
                },
                "veranstaltungen": {
                    "ritter": False,
                    "pro": False,
                    "andere": ""
                },
                "skripte": {
                    "lukasch": False,
                    "limant": False,
                    "andere": ""
                },
                "quantum": {
                    "albrecht": False,
                    "roithmaier": False,
                    "andere": ""
                },
                "kooperationen": {
                    "winckler": False,
                    "andere": ""
                },
                "it": {
                    "kalk": False,
                    "sittig": False,
                    "andere": ""
                },
                "evaluationen": {
                    "reichelt": False,
                    "andere": ""
                },
                "hochschulpolitik": {
                    "armbruster": False,
                    "paulus": False,
                    "andere": ""
                },
                "finanzen": {
                    "spicker": False,
                    "schuh": False,
                    "andere": ""
                },
                "pr": {
                    "werle": False,
                    "andere": ""
                }
            }
        }
    }

    print(validate(example_1))
