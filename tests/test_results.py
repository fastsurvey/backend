import app.main as main
import app.results as results


def test_adding_email_to_aggregation_pipeline(test_surveys):
    """Test adding an email field to the aggregation pipeline."""
    configuration = test_surveys['email']['configuration']
    alligator = results.Alligator(configuration, main.database)
    alligator._add_email(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {}
    assert alligator.group == {
        '_id': 'fastsurvey.email',
        'count': {'$sum': 1},
    }


def test_adding_option_to_aggregation_pipeline(test_surveys):
    """Test adding an option field to the aggregation pipeline."""
    configuration = test_surveys['option']['configuration']
    alligator = results.Alligator(configuration, main.database)
    alligator._add_option(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {
        'data.1': {'$toInt': '$data.1'},
    }
    assert alligator.group == {
        '_id': 'fastsurvey.option',
        'count': {'$sum': 1},
        '1': {'$sum': '$data.1'},
    }


def test_adding_radio_to_aggregation_pipeline(test_surveys):
    """Test adding a radio field to the aggregation pipeline."""
    configuration = test_surveys['radio']['configuration']
    alligator = results.Alligator(configuration, main.database)
    alligator._add_radio(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {
        'data.1.1': {'$toInt': '$data.1.1'},
        'data.1.2': {'$toInt': '$data.1.2'},
        'data.1.3': {'$toInt': '$data.1.3'},
        'data.1.4': {'$toInt': '$data.1.4'},
    }
    assert alligator.group == {
        '_id': 'fastsurvey.radio',
        'count': {'$sum': 1},
        '1+1': {'$sum': '$data.1.1'},
        '1+2': {'$sum': '$data.1.2'},
        '1+3': {'$sum': '$data.1.3'},
        '1+4': {'$sum': '$data.1.4'},
    }


def test_adding_selection_to_aggregation_pipeline(test_surveys):
    """Test adding a selection field to the aggregation pipeline."""
    configuration = test_surveys['selection']['configuration']
    alligator = results.Alligator(configuration, main.database)
    alligator._add_radio(
        field=configuration['fields'][0],
        index=2,
    )
    assert alligator.project == {
        'data.2.1': {'$toInt': '$data.2.1'},
        'data.2.2': {'$toInt': '$data.2.2'},
        'data.2.3': {'$toInt': '$data.2.3'},
    }
    assert alligator.group == {
        '_id': 'fastsurvey.selection',
        'count': {'$sum': 1},
        '2+1': {'$sum': '$data.2.1'},
        '2+2': {'$sum': '$data.2.2'},
        '2+3': {'$sum': '$data.2.3'},
    }


def test_adding_text_to_aggregation_pipeline(test_surveys):
    """Test adding a text field to the aggregation pipeline."""
    configuration = test_surveys['text']['configuration']
    alligator = results.Alligator(configuration, main.database)
    alligator._add_text(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {}
    assert alligator.group == {
        '_id': 'fastsurvey.text',
        'count': {'$sum': 1},
    }
