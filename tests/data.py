import os
import json


def _build_invalid_configurationss(test_survey_datas):
    test_survey_datas['invalid_configurationss'] = dict()
    with open(f'tests/data/surveys/complex/invalid_configurations.json', 'r') as e:
        test_survey_datas['invalid_configurationss']['complex'] = json.load(e)


def _build_invalid_submissionss(test_survey_datas):
    test_survey_datas['invalid_submissionss'] = dict()
    with open(f'tests/data/surveys/complex/invalid_submissions.json', 'r') as e:
        test_survey_datas['invalid_submissionss']['complex'] = json.load(e)


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
