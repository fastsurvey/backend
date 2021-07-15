import app.utils as utils
import app.resources.database as database


def _add_email_aggregation_commands(pipeline, field, index):
    """Add commands to aggregate email field to aggregation pipeline."""
    pass


def _add_option_aggregation_commands(pipeline, field, index):
    """Add commands to aggregate option field to aggregation pipeline."""
    path = f'data.{index}'
    pipeline[0]['$project'][path] = {'$toInt': f'${path}'}
    pipeline[1]['$group'][str(index)] = {'$sum': f'${path}'}


def _add_radio_aggregation_commands(pipeline, field, index):
    """Add commands to aggregate radio field to aggregation pipeline."""
    subfields = field['fields']
    for i in range(len(subfields)):
        path = f'data.{index}.{i+1}'
        pipeline[0]['$project'][path] = {'$toInt': f'${path}'}
        pipeline[1]['$group'][f'{index}+{i+1}'] = {'$sum': f'${path}'}


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
            '$project': {}
        },
        {
            '$group': {
                '_id': utils.identify(configuration),
                'count': {'$sum': 1},
            },
        },
#       {
#           '$merge': {
#               'into': 'resultss',
#               'on': '_id',
#               'whenMatched': 'replace',
#               'whenNotMatched': 'insert',
#           },
#       },
    ]
    for index, field in enumerate(configuration['fields']):
        FMAP[field['type']](aggregation_pipeline, field, index+1)
    if not aggregation_pipeline[0]['$project']:
        aggregation_pipeline.pop(0)
    return aggregation_pipeline


def _structure_results(results):
    """Make planar results from MongoDB aggregation nested."""
    out = {}
    for key, value in results.items():
        if '+' in key:
            split = key.split('+', maxsplit=1)
            out.setdefault(split[0], {})
            out[split[0]][split[1]] = value
        else:
            out[key] = value
    return out


async def aggregate(configuration):
    """Aggregate and return the results of the survey."""
    survey_id = utils.identify(configuration)
    submissions = database.database[f'surveys.{survey_id}.submissions']
    cursor = submissions.aggregate(
        pipeline=_build_aggregation_pipeline(configuration),
        allowDiskUse=True,
    )
    results = (await cursor.to_list(length=None))[0]
    results.pop('_id')
    return _structure_results(results)
