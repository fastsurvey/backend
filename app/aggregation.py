import copy

import app.utils as utils
import app.resources.database as database


AGGREGATION_PIPELINE_BASE = [
    {
        '$facet': {
            'main': [
                {
                    '$group': {
                        '_id': None,
                        'count': {'$sum': 1},
                    },
                },
            ],
        },
    },
    {
        '$project': {
            'count': {'$first': '$main.count'},
            'data': {}
        },
    },
]


def _add_email_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate email submissions."""
    pipeline[1]['$project']['data'][identifier] = None


def _add_option_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate options submissions."""
    pipeline[0]['$facet']['main'][0]['$group'][identifier] = {
        '$sum': {'$toInt': f'$data.{identifier}'}
    }
    pipeline[1]['$project']['data'][identifier] = {
        '$first': f'$main.{identifier}',
    }


def _add_radio_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate radio submissions."""
    pipeline[0]['$facet'][identifier] = [
        {
            '$group': {
                '_id': f'$data.{identifier}',
                'count': {
                    '$sum': 1,
                },
            },
        },
        {
            '$group': {
                '_id': None,
                identifier: {
                    '$push': {
                        'k': '$_id',
                        'v': '$count',
                    },
                },
            },
        },
        {
            '$project': {
                identifier: {
                    '$arrayToObject': f'${identifier}',
                },
            },
        },
    ]
    pipeline[1]['$project']['data'][identifier] = {
        '$first': f'${identifier}.{identifier}',
    }


def _add_selection_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate selection submissions."""
    _add_radio_aggregation_commands(pipeline, identifier)
    pipeline[0]['$facet'][identifier].insert(
        0,
        {
            '$unwind': {
                'path': f'$data.{identifier}',
            },
        },
    )


def _add_text_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate text submissions."""
    _add_email_aggregation_commands(pipeline, identifier)


def _build_aggregation_pipeline(configuration):
    """Build MongoDB aggregation pipeline to aggregate survey submissions."""
    aggregation_pipeline = copy.deepcopy(AGGREGATION_PIPELINE_BASE)
    functions = {
        'email': _add_email_aggregation_commands,
        'option': _add_option_aggregation_commands,
        'radio': _add_radio_aggregation_commands,
        'selection': _add_selection_aggregation_commands,
        'text': _add_text_aggregation_commands,
    }
    for identifier, field in enumerate(configuration['fields']):
        functions[field['type']](aggregation_pipeline, str(identifier))
    return aggregation_pipeline


def _build_default_results(configuration):
    """Build default results to return when there are no submissions."""
    results = {'count': 0, 'data': {}}
    for identifier, field in enumerate(configuration['fields']):
        identifier = str(identifier)
        if field['type'] == 'option':
            results['data'][identifier] = 0
        elif field['type'] in ['radio', 'selection']:
            results['data'][identifier] = {
                option: 0 for option in field['options']
            }
        else:
            results['data'][identifier] = None
    return results


def _format_results(results, configuration):
    """Format results obtained from the MongoDB aggregation."""
    for identifier, field in enumerate(configuration['fields']):
        identifier = str(identifier)
        # add options that received no submissions and sort options as
        # specified in the configuration
        if field['type'] in ['radio', 'selection']:
            out = dict()
            for option in field['options']:
                out[option] = results['data'][identifier].get(option, 0)
            results['data'][identifier] = out
    return results


async def aggregate(configuration):
    """Aggregate and return the results of the survey."""
    survey_id = utils.identify(configuration)
    submissions = database.database[f'surveys.{survey_id}.submissions']
    cursor = submissions.aggregate(
        pipeline=_build_aggregation_pipeline(configuration),
        allowDiskUse=True,
    )
    results = await cursor.to_list(length=None)
    if 'count' in results[0]:
        return _format_results(results[0], configuration)
    return _build_default_results(configuration)
