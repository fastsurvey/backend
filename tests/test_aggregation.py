import app.main as main
import app.aggregation as aggregation
import app.utils as utils


def test_adding_email_to_aggregation_pipeline(admin_name, configurations):
    """Test adding an email field to the aggregation pipeline."""
    configuration = configurations['email']
    alligator = aggregation.Alligator(
        utils.combine(admin_name, configuration['survey_name']),
        {'admin_name': admin_name, **configuration},
        main.database,
    )
    alligator._add_email(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {}
    assert alligator.group == {
        '_id': f'{admin_name}.email',
        'count': {'$sum': 1},
    }


def test_adding_option_to_aggregation_pipeline(admin_name, configurations):
    """Test adding an option field to the aggregation pipeline."""
    configuration = configurations['option']
    alligator = aggregation.Alligator(
        utils.combine(admin_name, configuration['survey_name']),
        {'admin_name': admin_name, **configuration},
        main.database,
    )
    alligator._add_option(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {
        'data.1': {'$toInt': '$data.1'},
    }
    assert alligator.group == {
        '_id': f'{admin_name}.option',
        'count': {'$sum': 1},
        '1': {'$sum': '$data.1'},
    }


def test_adding_radio_to_aggregation_pipeline(admin_name, configurations):
    """Test adding a radio field to the aggregation pipeline."""
    configuration = configurations['radio']
    alligator = aggregation.Alligator(
        utils.combine(admin_name, configuration['survey_name']),
        {'admin_name': admin_name, **configuration},
        main.database,
    )
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
        '_id': f'{admin_name}.radio',
        'count': {'$sum': 1},
        '1+1': {'$sum': '$data.1.1'},
        '1+2': {'$sum': '$data.1.2'},
        '1+3': {'$sum': '$data.1.3'},
        '1+4': {'$sum': '$data.1.4'},
    }


def test_adding_selection_to_aggregation_pipeline(admin_name, configurations):
    """Test adding a selection field to the aggregation pipeline."""
    configuration = configurations['selection']
    alligator = aggregation.Alligator(
        utils.combine(admin_name, configuration['survey_name']),
        {'admin_name': admin_name, **configuration},
        main.database,
    )
    alligator._add_selection(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {
        'data.1.1': {'$toInt': '$data.1.1'},
        'data.1.2': {'$toInt': '$data.1.2'},
        'data.1.3': {'$toInt': '$data.1.3'},
    }
    assert alligator.group == {
        '_id': f'{admin_name}.selection',
        'count': {'$sum': 1},
        '1+1': {'$sum': '$data.1.1'},
        '1+2': {'$sum': '$data.1.2'},
        '1+3': {'$sum': '$data.1.3'},
    }


def test_adding_text_to_aggregation_pipeline(admin_name, configurations):
    """Test adding a text field to the aggregation pipeline."""
    configuration = configurations['text']
    alligator = aggregation.Alligator(
        utils.combine(admin_name, configuration['survey_name']),
        {'admin_name': admin_name, **configuration},
        main.database,
    )
    alligator._add_text(
        field=configuration['fields'][0],
        index=1,
    )
    alligator._add_text(
        field=configuration['fields'][0],
        index=1,
    )
    assert alligator.project == {}
    assert alligator.group == {
        '_id': f'{admin_name}.text',
        'count': {'$sum': 1},
    }
