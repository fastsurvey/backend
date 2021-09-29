import os
import json
import copy

import app.models as models


################################################################################
# Build Invalid Account Datas
################################################################################


def _build_invalid_account_datas(account_data):
    """Build invalid configurations from valid test survey configurations."""
    invalid_account_datas = []

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

    return invalid_account_datas


################################################################################
# Build Invalid Configurations
################################################################################


def _build_invalid_configurations(configuration):
    """Build some invalid configurations for the simple test survey."""
    invalid_configurations = []


    ####################################
    # Header Parameters
    ####################################


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
    # draft parameter has invalid type
    x = copy.deepcopy(configuration)
    x['draft'] = None
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
    # start parameter is missing
    x = copy.deepcopy(configuration)
    x.pop('start')
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
    # fields have duplicate identifiers
    x = copy.deepcopy(configuration)
    x['fields'][-1]['identifier'] = 2
    invalid_configurations.append(x)


    ####################################
    # Email Field
    ####################################


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


    ####################################
    # Option Field
    ####################################


    # required parameter has invalid type
    x = copy.deepcopy(configuration)
    x['fields'][1]['required'] = 1
    invalid_configurations.append(x)
    # type parameter is missing
    x = copy.deepcopy(configuration)
    x['fields'][1].pop('type')
    invalid_configurations.append(x)


    ####################################
    # Radio Field
    ####################################


    x = copy.deepcopy(configuration)
    x['fields'][2]['options'] = None
    invalid_configurations.append(x)
    # options parameter is missing
    x = copy.deepcopy(configuration)
    x['fields'][2].pop('options')
    invalid_configurations.append(x)
    # options are not unique
    x = copy.deepcopy(configuration)
    x['fields'][2]['options'] += x['fields'][2]['options'][0]
    invalid_configurations.append(x)
    # options list is empty
    x = copy.deepcopy(configuration)
    x['fields'][2]['options'] = []
    invalid_configurations.append(x)


    ####################################
    # Selection Field
    ####################################


    # options parameter has invalid type
    x = copy.deepcopy(configuration)
    x['fields'][3]['options'] = None
    invalid_configurations.append(x)
    # min_select parameter has invalid type
    x = copy.deepcopy(configuration)
    x['fields'][3]['min_select'] = float(x['fields'][3]['min_select'])
    invalid_configurations.append(x)
    # max_select parameter is missing
    x = copy.deepcopy(configuration)
    x['fields'][3].pop('max_select')
    invalid_configurations.append(x)
    # options are not unique
    x = copy.deepcopy(configuration)
    x['fields'][3]['options'] += x['fields'][3]['options'][0]
    invalid_configurations.append(x)
    # options list is empty
    x = copy.deepcopy(configuration)
    x['fields'][3]['options'] = []
    invalid_configurations.append(x)
    # min_select is greater than max_select
    x = copy.deepcopy(configuration)
    x['fields'][3]['min_select'] = x['fields'][3]['max_select'] + 1
    invalid_configurations.append(x)
    # min_select is less than zero
    x = copy.deepcopy(configuration)
    x['fields'][3]['min_select'] = -1
    invalid_configurations.append(x)
    # max_select is greater than number of options
    x = copy.deepcopy(configuration)
    x['fields'][3]['max_select'] = len(x['fields'][3]['options']) + 1
    invalid_configurations.append(x)


    ####################################
    # Text Field
    ####################################


    # min_chars parameter has invalid type
    x = copy.deepcopy(configuration)
    x['fields'][4]['min_chars'] = float(x['fields'][4]['min_chars'])
    invalid_configurations.append(x)
    # max_chars parameter is missing
    x = copy.deepcopy(configuration)
    x['fields'][4].pop('max_chars')
    invalid_configurations.append(x)
    # min_chars is greater than max_chars
    x = copy.deepcopy(configuration)
    x['fields'][4]['min_chars'] = x['fields'][4]['max_chars'] + 1
    invalid_configurations.append(x)
    # min_chars is less than zero
    x = copy.deepcopy(configuration)
    x['fields'][4]['min_chars'] = -1
    invalid_configurations.append(x)
    # max_chars is greater than character limit
    x = copy.deepcopy(configuration)
    x['fields'][4]['max_chars'] = models.Length.C + 1
    invalid_configurations.append(x)

    return invalid_configurations


################################################################################
# Build Invalid Submissions
################################################################################


def _build_invalid_submissions(submission):
    """Build some invalid submissions for the simple test survey."""
    invalid_submissions = []


    ####################################
    # General Structure
    ####################################


    # too many field inputs
    x = copy.deepcopy(submission)
    x['5'] = x['2']
    invalid_submissions.append(x)
    # input has missing identifier
    x = copy.deepcopy(submission)
    x.pop('3')
    invalid_submissions.append(x)
    # input has missing identifier
    invalid_submissions.append({})


    ####################################
    # Email Field
    ####################################


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


    ####################################
    # Option Field
    ####################################


    # input has invalid type
    x = copy.deepcopy(submission)
    x['1'] = 1
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['1'] = None
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['1'] = ''
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['1'] = False
    invalid_submissions.append(x)


    ####################################
    # Radio Field
    ####################################


    # input has invalid type
    x = copy.deepcopy(submission)
    x['2'] = True
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['2'] = 1
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['2'] = dict()
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['2'] = None
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['2'] = []
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['2'] = ''
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['2'] = 'Hello World!'
    invalid_submissions.append(x)


    ####################################
    # Selection Field
    ####################################


    # input has invalid type
    x = copy.deepcopy(submission)
    x['3'] = None
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['3'] = True
    invalid_submissions.append(x)
    # input has too many selected options
    x = copy.deepcopy(submission)
    x['3'] = ["Strawberry", "Vanilla", "Chocolate"]
    invalid_submissions.append(x)
    # input has not enough selected options
    x = copy.deepcopy(submission)
    x['3'] = []
    invalid_submissions.append(x)
    # input has duplicate selected options
    x = copy.deepcopy(submission)
    x['3'] = ["Strawberry", "Strawberry"]
    invalid_submissions.append(x)


    ####################################
    # Text Field
    ####################################


    # input has invalid type
    x = copy.deepcopy(submission)
    x['4'] = 42
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['4'] = None
    invalid_submissions.append(x)
    # input has invalid type
    x = copy.deepcopy(submission)
    x['4'] = ['Hello', 'World']
    invalid_submissions.append(x)
    # input has invalid value
    x = copy.deepcopy(submission)
    x['4'] = 'tomato'
    invalid_submissions.append(x)
    # text field input has invalid value
    x = copy.deepcopy(submission)
    x['4'] = ''
    invalid_submissions.append(x)
    # input has invalid value (more chars than allowed by max_chars)
    x = copy.deepcopy(submission)
    x['4'] = '+' * 1001
    invalid_submissions.append(x)

    return invalid_submissions


################################################################################
# Load Test Data
################################################################################


def _load_test_accounts_data():
    """Load some valid and invalid test examples of account data."""
    data = {}
    with open('tests/data/account_datas.json', 'r') as e:
        data['account_datas'] = json.load(e)
    data['invalid_account_datas'] = _build_invalid_account_datas(
        account_data=data['account_datas'][0],
    )
    return data


def _load_simple_test_survey_data():
    """Load test data of simple survey (configuration, submissions, ...)."""
    data = dict()
    parameters = [
        'configuration',
        'submissions',
        'aggregation_pipeline',
        'results',
        'default_results',
    ]
    for parameter in parameters:
        with open(f'tests/data/surveys/simple/{parameter}.json', 'r') as x:
            data[parameter] = json.load(x)
    data['invalid_configurations'] = _build_invalid_configurations(
        configuration=data['configuration'],
    )
    data['invalid_submissions'] = _build_invalid_submissions(
        submission=data['submissions'][0],
    )
    return data


def _load_complex_test_survey_data():
    """Load test data of complex survey, including some survey updates."""
    data = dict()
    for parameter in ['configurations', 'submissionss', 'resultss']:
        with open(f'tests/data/surveys/complex/{parameter}.json', 'r') as x:
            data[parameter] = json.load(x)
    return data


TEST_ACCOUNTS_DATA = _load_test_accounts_data()
SIMPLE_TEST_SURVEY_DATA = _load_simple_test_survey_data()
COMPLEX_TEST_SURVEY_DATA = _load_complex_test_survey_data()
