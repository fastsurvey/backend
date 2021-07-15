import app.utils as utils
import app.resources.database as database


def _add_email_aggregation_commands(pipeline, field, index):
    """Add commands to aggregate email field to aggregation pipeline."""
    pass


def _add_option_aggregation_commands(pipeline, field, index):
    """Add commands to aggregate option field to aggregation pipeline."""
    pipeline[0]['$group'][str(index)] = {
        '$sum': {
            '$toInt': f'$data.{index+1}',
        },
    }
    pipeline[1]['$project'][str(index)] = True


def _add_radio_aggregation_commands(pipeline, field, index):
    """Add commands to aggregate radio field to aggregation pipeline."""
    subfields = field['fields']
    for i in range(len(subfields)):
        pipeline[0]['$group'][f'{index}+{i}'] = {
            '$sum': {
                '$toInt': f'$data.{index+1}.{i+1}',
            },
        }
    pipeline[1]['$project'][str(index)] = [
        f'${index}+{i}'
        for i
        in range(len(subfields))
    ]


def _add_selection_aggregation_commands(pipeline, field, index):
    """Add commands to aggregate selection field to aggregation pipeline."""
    _add_radio_aggregation_commands(pipeline, field, index)


def _add_text_aggregation_commands(pipeline, field, index):
    """Add commands to aggregate text field to aggregation pipeline."""
    pass


FMAP = {
    'email': _add_email_aggregation_commands,
    'option': _add_option_aggregation_commands,
    'radio': _add_radio_aggregation_commands,
    'selection': _add_selection_aggregation_commands,
    'text': _add_text_aggregation_commands,
}


def _build_aggregation_pipeline(configuration):
    """Build pymongo aggregation pipeline to aggregate survey submissions."""
    aggregation_pipeline = [
        {
            '$group': {
                '_id': None,
                'count': {'$sum': 1},
            },
        },
        {
            '$project': {
                '_id': False,
                'count': True,
            }
        },
        {
            '$project': {
                'count': True,
                'data': [f'${i}' for i in range(len(configuration['fields']))],
            }
        },
    ]
    for index, field in enumerate(configuration['fields']):
        FMAP[field['type']](aggregation_pipeline, field, index)
    return aggregation_pipeline


def _build_default_value(field):
    """Build default field aggregation value for zero submissions."""
    if field['type'] == 'option':
        return 0
    if field['type'] in ['radio', 'selection']:
        return [0] * len(field['fields'])
    return None


def _build_default_results(configuration):
    """Build default results to return when there are no submissions."""
    return {
        'count': 0,
        'data': [
            _build_default_value(field)
            for field
            in configuration['fields']
        ]
    }


async def aggregate(configuration):
    """Aggregate and return the results of the survey."""
    survey_id = utils.identify(configuration)
    submissions = database.database[f'surveys.{survey_id}.submissions']
    cursor = submissions.aggregate(
        pipeline=_build_aggregation_pipeline(configuration),
        allowDiskUse=True,
    )
    results = await cursor.to_list(length=None)
    return results[0] if len(results) else _build_default_results(configuration)
