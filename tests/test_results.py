import app.main as main
import app.results as results


def test_adding_option_to_aggregation_pipeline(configurations):
    """Test adding an option field to the aggregation pipeline."""
    configuration = configurations['option']
    alligator = results.Alligator(configuration, main.database)
    alligator._add_option(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {
        'properties.1': {'$toInt': '$properties.1'},
    }
    assert alligator.group == {
        '_id': 'fastsurvey.option',
        'count': {'$sum': 1},
        '1': {'$sum': '$properties.1'},
    }


def test_adding_radio_to_aggregation_pipeline(configurations):
    """Test adding a radio field to the aggregation pipeline."""
    configuration = configurations['radio']
    alligator = results.Alligator(configuration, main.database)
    alligator._add_radio(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {
        'properties.1.1': {'$toInt': '$properties.1.1'},
        'properties.1.2': {'$toInt': '$properties.1.2'},
        'properties.1.3': {'$toInt': '$properties.1.3'},
        'properties.1.4': {'$toInt': '$properties.1.4'},
    }
    assert alligator.group == {
        '_id': 'fastsurvey.radio',
        'count': {'$sum': 1},
        '1-1': {'$sum': '$properties.1.1'},
        '1-2': {'$sum': '$properties.1.2'},
        '1-3': {'$sum': '$properties.1.3'},
        '1-4': {'$sum': '$properties.1.4'},
    }


def test_adding_selection_to_aggregation_pipeline(configurations):
    """Test adding a selection field to the aggregation pipeline."""
    configuration = configurations['selection']
    alligator = results.Alligator(configuration, main.database)
    alligator._add_radio(
        field=configuration['fields'][0],
        index=2,
    )
    assert alligator.project == {
        'properties.2.1': {'$toInt': '$properties.2.1'},
        'properties.2.2': {'$toInt': '$properties.2.2'},
        'properties.2.3': {'$toInt': '$properties.2.3'},
    }
    assert alligator.group == {
        '_id': 'fastsurvey.selection',
        'count': {'$sum': 1},
        '2-1': {'$sum': '$properties.2.1'},
        '2-2': {'$sum': '$properties.2.2'},
        '2-3': {'$sum': '$properties.2.3'},
    }
