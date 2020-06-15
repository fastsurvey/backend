import pytest
import copy

from .. import main
from .. import results


def test_add_radio(survey):
    """Test that radio field is correctly added to the pipeline."""
    survey.alligator._add_radio(
        field=survey.cn['fields'][0],
        index=1,
    )
    assert survey.alligator.project == {
        'properties.1.1': {'$toInt': '$properties.1.1'},
        'properties.1.2': {'$toInt': '$properties.1.2'},
    }
    assert survey.alligator.group == {
        '_id': 'fastsurvey.test',
        'count': {'$sum': 1},
        '1-1': {'$sum': '$properties.1.1'},
        '1-2': {'$sum': '$properties.1.2'},
    }


def test_add_selection(survey):
    """Test that radio field is correctly added to the pipeline."""
    import json
    print(json.dumps(survey.alligator.project, indent=4))
    survey.alligator._add_selection(
        field=survey.cn['fields'][1],
        index=2,
    )
    assert survey.alligator.project == {
        'properties.2.1': {'$toInt': '$properties.2.1'},
        'properties.2.2': {'$toInt': '$properties.2.2'},
        'properties.2.3': {'$toInt': '$properties.2.3'},
    }
    assert survey.alligator.group == {
        '_id': 'fastsurvey.test',
        'count': {'$sum': 1},
        '2-1': {'$sum': '$properties.2.1'},
        '2-2': {'$sum': '$properties.2.2'},
        '2-3': {'$sum': '$properties.2.3'},
    }
