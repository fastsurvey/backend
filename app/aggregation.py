import copy


AGGREGATION_PIPELINE_BASE = [
    {
        "$facet": {
            "main": [
                {
                    "$group": {"_id": None, "count": {"$sum": 1}},
                },
            ],
        },
    },
    {
        "$project": {
            "count": {"$first": "$main.count"},
        },
    },
]


def _add_markdown_field_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate markdown field submissions."""
    pass


def _add_email_field_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate email field submissions."""
    pipeline[0]["$facet"]["main"][0]["$group"][f"{identifier}+count"] = {
        "$sum": {
            "$toInt": {"$ne": [{"$type": f"$submission.{identifier}"}, "missing"]}
        },
    }
    pipeline[1]["$project"][identifier] = {
        "count": {"$first": f"$main.{identifier}+count"},
        "value": None,
    }


def _add_selection_field_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate selection field submissions."""
    pipeline[0]["$facet"]["main"][0]["$group"][f"{identifier}+count"] = {
        "$sum": {
            "$toInt": {"$ne": [{"$type": f"$submission.{identifier}"}, "missing"]}
        },
    }
    pipeline[0]["$facet"][f"a{identifier}"] = [
        {
            "$unwind": {
                "path": f"$submission.{identifier}",
            },
        },
        {
            "$group": {
                "_id": f"$submission.{identifier}",
                "count": {"$sum": 1},
            },
        },
        {
            "$group": {
                "_id": None,
                "value": {"$push": {"k": "$_id", "v": "$count"}},
            },
        },
        {
            "$project": {
                "value": {"$arrayToObject": f"$value"},
            },
        },
    ]
    pipeline[1]["$project"][identifier] = {
        "count": {"$first": f"$main.{identifier}+count"},
        "value": {"$first": f"$a{identifier}.value"},
    }


def _add_page_break_field_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate page break field submissions."""
    pass


def _add_text_field_aggregation_commands(pipeline, identifier):
    """Add pipeline commands to aggregate text field submissions."""
    _add_email_field_aggregation_commands(pipeline, identifier)


def _build_aggregation_pipeline(configuration):
    """Build MongoDB aggregation pipeline to aggregate survey submissions."""
    pipeline = copy.deepcopy(AGGREGATION_PIPELINE_BASE)
    functions = {
        "markdown": _add_markdown_field_aggregation_commands,
        "email": _add_email_field_aggregation_commands,
        "selection": _add_selection_field_aggregation_commands,
        "break": _add_page_break_field_aggregation_commands,
        "text": _add_text_field_aggregation_commands,
    }
    for field in configuration["fields"]:
        functions[field["type"]](pipeline, str(field["identifier"]))
    return pipeline


def _format_results(results, configuration):
    """Format results obtained from the MongoDB aggregation."""
    results.setdefault("count", 0)
    for field in configuration["fields"]:
        identifier = str(field["identifier"])
        if field["type"] in ["email", "text"]:
            results[identifier].setdefault("count", 0)
            results[identifier].setdefault("value", None)
        # add options that received no submissions and sort options as specified in the
        # configuration; options that were previously selected, but have been removed
        # from the configuration are not returned; this makes results less transparent
        # in favor of making the results of updated surveys less confusing
        elif field["type"] == "selection":
            results[identifier].setdefault("count", 0)
            results[identifier].setdefault("value", {})
            out = dict()
            for option in field["options"]:
                out[option] = results[identifier]["value"].get(option, 0)
            results[identifier]["value"] = out
    return results


async def aggregate(submissions, configuration):
    """Compute an aggregate of the submissions of a survey."""
    cursor = submissions.aggregate(
        pipeline=_build_aggregation_pipeline(configuration),
        allowDiskUse=True,
    )
    results = await cursor.to_list(length=None)
    return _format_results(results[0], configuration)
