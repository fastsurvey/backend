import os
import json
import copy

import app.models as models


################################################################################
# Build Invalid Account Datas
################################################################################


def _build_invalid_account_datas(test_account_documentss):
    """Build invalid configurations from valid test survey configurations."""
    invalid_account_datas = []
    account_data = test_account_documentss['account_datas'][0]
    # username parameter has invalid type
    x = copy.deepcopy(account_data)
    x['username'] = None
    invalid_account_datas.append(x)
    # email_address parameter has invalid type
    x = copy.deepcopy(account_data)
    x['email_address'] = 42
    invalid_account_datas.append(x)
    # password parameter has invalid type
    x = copy.deepcopy(account_data)
    x['password'] = None
    invalid_account_datas.append(x)
    # email_address parameter has invalid value
    x = copy.deepcopy(account_data)
    x['email_address'] = 'email'
    invalid_account_datas.append(x)
    # username parameter has invalid value
    x = copy.deepcopy(account_data)
    x['username'] = ''
    invalid_account_datas.append(x)
    # password parameter has invalid value
    x = copy.deepcopy(account_data)
    x['password'] = '1234'
    invalid_account_datas.append(x)
    # password parameter has invalid value
    x = copy.deepcopy(account_data)
    x['password'] = '#' * (models.Length.B + 1)
    invalid_account_datas.append(x)
    # email_address parameter is missing
    x = copy.deepcopy(account_data)
    x.pop('email_address')
    invalid_account_datas.append(x)
    # unsolicited parameter
    x = copy.deepcopy(account_data)
    x['admin'] = True
    invalid_account_datas.append(x)

    test_account_documentss['invalid_account_datas'] = invalid_account_datas


################################################################################
# Build Invalid Configurations
################################################################################


def _build_invalid_configurationss(test_survey_documentss):
    """Build invalid configurations from valid test survey configurations."""
    test_survey_documentss['invalid_configurationss'] = dict()
    configurations = test_survey_documentss['configurations']
    FMAP = {
        'complex': _build_invalid_complex_configurations,
        'option': _build_invalid_option_configurations,
        'radio': _build_invalid_radio_configurations,
        'selection': _build_invalid_selection_configurations,
        'text': _build_invalid_text_configurations,
        'email': _build_invalid_email_configurations,
    }
    for survey_name, configuration in configurations.items():
        test_survey_documentss['invalid_configurationss'][survey_name] = (
            FMAP[survey_name](configuration)
        )


def _build_invalid_complex_configurations(configuration):
    """Build some invalid configurations for the complex test survey.

    With this general survey we mostly test the validation of the header
    fields. With the other, more specific, test surveys we test the individual
    field validations.

    """
    invalid_configurations = []
    # limit parameter has invalid type
    x = copy.deepcopy(configuration)
    x['limit'] = True
    invalid_configurations.append(x)
    # limit parameter has invalid type
    x = copy.deepcopy(configuration)
    x['limit'] = 3.14
    invalid_configurations.append(x)
    # start parameter has invalid type
    x = copy.deepcopy(configuration)
    x['start'] = ''
    invalid_configurations.append(x)
    # start parameter has invalid type
    x = copy.deepcopy(configuration)
    x['start'] = 3.14
    invalid_configurations.append(x)
    # start parameter has invalid type
    x = copy.deepcopy(configuration)
    x['start'] = None
    invalid_configurations.append(x)
    # fields parameter has invalid type
    x = copy.deepcopy(configuration)
    x['fields'] = None
    invalid_configurations.append(x)
    # end parameter has invalid value
    x = copy.deepcopy(configuration)
    x['end'] = 4102444801
    invalid_configurations.append(x)
    # survey_name parameter has invalid value
    x = copy.deepcopy(configuration)
    x['survey_name'] = '$' * 8
    invalid_configurations.append(x)
    # title parameter has invalid value
    x = copy.deepcopy(configuration)
    x['title'] = '@' * (models.Length.B + 1)
    invalid_configurations.append(x)
    # description parameter has invalid value
    x = copy.deepcopy(configuration)
    x['description'] = '+' * (models.Length.C + 1)
    invalid_configurations.append(x)
    # draft parameter is missing
    x = copy.deepcopy(configuration)
    x.pop('draft')
    invalid_configurations.append(x)
    # field list is empty
    x = copy.deepcopy(configuration)
    x['fields'] = []
    invalid_configurations.append(x)
    # field item is empty
    x = copy.deepcopy(configuration)
    x['fields'][2] = {}
    invalid_configurations.append(x)
    # field item has invalid type
    x = copy.deepcopy(configuration)
    x['fields'][2] = 42
    invalid_configurations.append(x)

    return invalid_configurations


def _build_invalid_option_configurations(configuration):
    """Build some invalid configurations for the option test survey."""
    invalid_configurations = []
    # required parameter has invalid type
    x = copy.deepcopy(configuration)
    x['fields'][0]['required'] = 1
    invalid_configurations.append(x)
    # type parameter is missing
    x = copy.deepcopy(configuration)
    x['fields'][0].pop('type')
    invalid_configurations.append(x)

    return invalid_configurations


def _build_invalid_radio_configurations(configuration):
    """Build some invalid configurations for the radio test survey."""
    return []


def _build_invalid_selection_configurations(configuration):
    """Build some invalid configurations for the selection test survey."""
    return []


def _build_invalid_text_configurations(configuration):
    """Build some invalid configurations for the text test survey."""
    return []


def _build_invalid_email_configurations(configuration):
    """Build some invalid configurations for the email test survey."""
    invalid_configurations = []
    # more than one email field to verify
    x = copy.deepcopy(configuration)
    x['fields'].append(x['fields'][0])
    invalid_configurations.append(x)
    # verify parameter has invalid type
    x = copy.deepcopy(configuration)
    x['fields'][0]['verify'] = 1
    invalid_configurations.append(x)
    # type parameter has invalid value
    x = copy.deepcopy(configuration)
    x['fields'][0]['type'] = 'text'
    invalid_configurations.append(x)
    # type parameter has invalid value
    x = copy.deepcopy(configuration)
    x['fields'][0]['type'] = 'EMAIL'
    invalid_configurations.append(x)
    # regex parameter has invalid regex
    x = copy.deepcopy(configuration)
    x['fields'][0]['regex'] = '*'
    invalid_configurations.append(x)
    # regex parameter has invalid value
    x = copy.deepcopy(configuration)
    x['fields'][0]['regex'] = None
    invalid_configurations.append(x)
    # hint parameter has invalid value
    x = copy.deepcopy(configuration)
    x['fields'][0]['hint'] = '$' * (models.Length.B + 1)
    invalid_configurations.append(x)

    return invalid_configurations


################################################################################
# Build Invalid Submissions
################################################################################


def _build_invalid_submissionss(test_survey_datas):
    """Build invalid submissions from valid test survey submissions."""
    test_survey_datas['invalid_submissionss'] = dict()
    submissionss = test_survey_datas['submissionss']
    FMAP = {
        'complex': _build_invalid_complex_submissions,
        'option': _build_invalid_option_submissions,
        'radio': _build_invalid_radio_submissions,
        'selection': _build_invalid_selection_submissions,
        'text': _build_invalid_text_submissions,
        'email': _build_invalid_email_submissions,
    }
    for survey_name, submissions in submissionss.items():
        test_survey_datas['invalid_submissionss'][survey_name] = (
            FMAP[survey_name](submissions[0])
        )


def _build_invalid_complex_submissions(submission):
    """Build some invalid submissions for the complex test survey."""
    invalid_submissions = []
    # radio field input has invalid type
    x = copy.deepcopy(submission)
    x['2'] = None
    invalid_submissions.append(x)
    # text field input has invalid value
    x = copy.deepcopy(submission)
    x['4'] = ''
    invalid_submissions.append(x)
    # text field input is missing
    x = copy.deepcopy(submission)
    x.pop('4')
    invalid_submissions.append(x)
    # too many field inputs
    x = copy.deepcopy(submission)
    x['5'] = x['2']
    invalid_submissions.append(x)

    return invalid_submissions


def _build_invalid_option_submissions(submission):
    """Build some invalid submissions for the option test survey."""
    invalid_submissions = []
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = 1
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = None
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['0'] = ''
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['0'] = False
    invalid_submissions.append(x)
    # input has wrong identifier
    x = copy.deepcopy(submission)
    x['email'] = x['0']
    x.pop('0')
    invalid_submissions.append(x)

    return invalid_submissions


def _build_invalid_radio_submissions(submission):
    """Build some invalid submissions for the radio test survey."""
    invalid_submissions = []
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = True
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = 1
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = dict()
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = None
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = []
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['0'] = ''
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['0'] = 'Hello World!'
    invalid_submissions.append(x)
    # input has wrong identifier
    x = copy.deepcopy(submission)
    x['42'] = x['0']
    x.pop('0')
    invalid_submissions.append(x)

    return invalid_submissions


def _build_invalid_selection_submissions(submission):
    """Build some invalid submissions for the selection test survey."""
    invalid_submissions = []
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = None
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = True
    invalid_submissions.append(x)
    # input has missing identifier
    x = copy.deepcopy(submission)
    x.pop('0')
    invalid_submissions.append(x)
    # input has too many selected options
    x = copy.deepcopy(submission)
    x['0'] = ["Strawberry", "Vanilla", "Chocolate"]
    invalid_submissions.append(x)
    # input has not enough selected options
    x = copy.deepcopy(submission)
    x['0'] = []
    invalid_submissions.append(x)
    # input has duplicate selected options
    x = copy.deepcopy(submission)
    x['0'] = ["Strawberry", "Strawberry"]
    invalid_submissions.append(x)

    return invalid_submissions


def _build_invalid_text_submissions(submission):
    """Build some invalid submissions for the text test survey."""
    invalid_submissions = []
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = 42
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = None
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = ['Hello', 'World']
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['0'] = 'tomato'
    invalid_submissions.append(x)
    # input has invalid value (more chars than allowed by max_chars)
    x = copy.deepcopy(submission)
    x['0'] = '+' * 1001
    invalid_submissions.append(x)
    # input has missing identifier
    invalid_submissions.append({})

    return invalid_submissions


def _build_invalid_email_submissions(submission):
    """Build some invalid submissions for the email test survey."""
    invalid_submissions = []
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = 42
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = None
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['0'] = 3.14
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['0'] = ''
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['0'] = ':' * (models.Length.B + 1)
    invalid_submissions.append(x)
    # input has wrong identifier
    x = copy.deepcopy(submission)
    x['email'] = x['0']
    x.pop('0')
    invalid_submissions.append(x)

    return invalid_submissions


################################################################################
# Load Test Data
################################################################################


def _load_test_account_documentss():
    """Load some valid and invalid test examples of account data."""
    documentss = {}
    with open('tests/data/account_datas.json', 'r') as e:
        documentss['account_datas'] = json.load(e)

    _build_invalid_account_datas(documentss)
    return documentss


def _load_test_survey_documentss():
    """Load test survey data (configurations, submissions, ...)."""
    folder = 'tests/data/surveys'
    survey_names = [s for s in os.listdir(folder) if s[0] != '.']
    documentss = {
        'configurations': dict(),
        'submissionss': dict(),
        'aggregation_pipelines': dict(),
        'resultss': dict(),
        'default_resultss': dict(),
    }
    for survey_name in survey_names:
        subfolder = f'{folder}/{survey_name}'
        for parameter_name, parameter_dict in documentss.items():
            with open(f'{subfolder}/{parameter_name[:-1]}.json', 'r') as e:
                parameter_dict[survey_name] = json.load(e)

    _build_invalid_configurationss(documentss)
    _build_invalid_submissionss(documentss)
    return documentss


TEST_ACCOUNT_DOCUMENTSS = _load_test_account_documentss()
TEST_SURVEY_DOCUMENTSS = _load_test_survey_documentss()
