import pytest
import copy

from .. import main
from .. import results


@pytest.fixture(scope='function')
async def cleanup(survey):
    """Reinstantiate the alligator class to clean up after a test."""
    yield
    survey.alligator = results.Alligator(survey.cn, main.database)


def test_add_radio(survey, cleanup):
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
