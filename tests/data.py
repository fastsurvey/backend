import os
import json
import copy


################################################################################
# Invalid Configurations
################################################################################


def _build_invalid_configurationss(test_survey_datas):
    """Build invalid configurations from valid test survey configurations."""
    test_survey_datas['invalid_configurationss'] = dict()
    configurations = test_survey_datas['configurations']
    FMAP = {
        'complex': _build_invalid_complex_configurations,
        'option': _build_invalid_option_configurations,
        'radio': _build_invalid_radio_configurations,
        'selection': _build_invalid_selection_configurations,
        'text': _build_invalid_text_configurations,
        'email': _build_invalid_email_configurations,
    }
    for survey_name, configuration in configurations.items():
        test_survey_datas['invalid_configurationss'][survey_name] = (
            FMAP[survey_name](configuration)
        )


def _build_invalid_complex_configurations(configuration):
    """Build some invalid configurations for the complex test survey."""
    invalid_configurations = []
    # invalid limit type
    x = copy.deepcopy(configuration)
    x['limit'] = True
    invalid_configurations.append(x)

    return invalid_configurations


def _build_invalid_option_configurations(configuration):
    """Build some invalid configurations for the option test survey."""
    pass


def _build_invalid_radio_configurations(configuration):
    """Build some invalid configurations for the radio test survey."""
    pass


def _build_invalid_selection_configurations(configuration):
    """Build some invalid configurations for the selection test survey."""
    pass


def _build_invalid_text_configurations(configuration):
    """Build some invalid configurations for the text test survey."""
    pass


def _build_invalid_email_configurations(configuration):
    """Build some invalid configurations for the email test survey."""
    pass


################################################################################
# Invalid Submissions
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
    # radio field input has wrong type
    x = copy.deepcopy(submission)
    x['3']['3'] = None
    invalid_submissions.append(x)
    # text field input not long enough
    x = copy.deepcopy(submission)
    x['5'] = ''
    invalid_submissions.append(x)

    return invalid_submissions


def _build_invalid_option_submissions(submission):
    """Build some invalid submissions for the option test survey."""
    pass


def _build_invalid_radio_submissions(submission):
    """Build some invalid submissions for the radio test survey."""
    pass


def _build_invalid_selection_submissions(submission):
    """Build some invalid submissions for the selection test survey."""
    pass


def _build_invalid_text_submissions(submission):
    """Build some invalid submissions for the text test survey."""
    pass


def _build_invalid_email_submissions(submission):
    """Build some invalid submissions for the email test survey."""
    pass


################################################################################
# Load Test Data
################################################################################


def _load_test_survey_datas():
    """Load test survey data (configurations, submissions, ...)."""
    folder = 'tests/data/surveys'
    survey_names = [s for s in os.listdir(folder) if s[0] != '.']
    test_survey_datas = {
        'configurations': dict(),
        'submissionss': dict(),
        'schemas': dict(),
        'aggregation_pipelines': dict(),
        'resultss': dict(),
    }
    for survey_name in survey_names:

        if survey_name != 'complex':
            continue

        subfolder = f'{folder}/{survey_name}'
        for parameter_name, parameter_dict in test_survey_datas.items():
            with open(f'{subfolder}/{parameter_name[:-1]}.json', 'r') as e:
                parameter_dict[survey_name] = json.load(e)

    _build_invalid_configurationss(test_survey_datas)
    _build_invalid_submissionss(test_survey_datas)
    return test_survey_datas


TEST_SURVEY_DATAS = _load_test_survey_datas()
TEST_ACCOUNT_DATAS = None
