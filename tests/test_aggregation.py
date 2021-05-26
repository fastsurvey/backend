import app.aggregation as aggregation


def test_adding_email_to_aggregation_pipeline(username, configurationss):
    """Test adding an email field to the aggregation pipeline."""
    configuration = configurationss['email']['valid']
    alligator = aggregation.Alligator({'username': username, **configuration})
    alligator._add_email(configuration['fields'][0], index=1)
    assert alligator.project == {}
    assert alligator.group == {
        '_id': f'{username}.email',
        'count': {'$sum': 1},
    }


def test_adding_option_to_aggregation_pipeline(username, configurationss):
    """Test adding an option field to the aggregation pipeline."""
    configuration = configurationss['option']['valid']
    alligator = aggregation.Alligator({'username': username, **configuration})
    alligator._add_option(configuration['fields'][0], index=1)
    assert alligator.project == {
        'data.1': {'$toInt': '$data.1'},
    }
    assert alligator.group == {
        '_id': f'{username}.option',
        'count': {'$sum': 1},
        '1': {'$sum': '$data.1'},
    }


def test_adding_radio_to_aggregation_pipeline(username, configurationss):
    """Test adding a radio field to the aggregation pipeline."""
    configuration = configurationss['radio']['valid']
    alligator = aggregation.Alligator({'username': username, **configuration})
    alligator._add_radio(configuration['fields'][0], index=1)
    assert alligator.project == {
        'data.1.1': {'$toInt': '$data.1.1'},
        'data.1.2': {'$toInt': '$data.1.2'},
        'data.1.3': {'$toInt': '$data.1.3'},
        'data.1.4': {'$toInt': '$data.1.4'},
    }
    assert alligator.group == {
        '_id': f'{username}.radio',
        'count': {'$sum': 1},
        '1+1': {'$sum': '$data.1.1'},
        '1+2': {'$sum': '$data.1.2'},
        '1+3': {'$sum': '$data.1.3'},
        '1+4': {'$sum': '$data.1.4'},
    }


def test_adding_selection_to_aggregation_pipeline(username, configurationss):
    """Test adding a selection field to the aggregation pipeline."""
    configuration = configurationss['selection']['valid']
    alligator = aggregation.Alligator({'username': username, **configuration})
    alligator._add_selection(configuration['fields'][0], index=1)
    assert alligator.project == {
        'data.1.1': {'$toInt': '$data.1.1'},
        'data.1.2': {'$toInt': '$data.1.2'},
        'data.1.3': {'$toInt': '$data.1.3'},
    }
    assert alligator.group == {
        '_id': f'{username}.selection',
        'count': {'$sum': 1},
        '1+1': {'$sum': '$data.1.1'},
        '1+2': {'$sum': '$data.1.2'},
        '1+3': {'$sum': '$data.1.3'},
    }


def test_adding_text_to_aggregation_pipeline(username, configurationss):
    """Test adding a text field to the aggregation pipeline."""
    configuration = configurationss['text']['valid']
    alligator = aggregation.Alligator({'username': username, **configuration})
    alligator._add_text(configuration['fields'][0], index=1)
    assert alligator.project == {}
    assert alligator.group == {
        '_id': f'{username}.text',
        'count': {'$sum': 1},
    }
