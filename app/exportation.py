import pymongo


def _build_aggregation_pipeline(configuration):
    """Build aggregation pipeline to uniformly export survey submissions."""
    pipeline = [
        {"$sort": {"submission_time": pymongo.ASCENDING}},
        {"$project": {"_id": False, "submission_time": True}},
    ]
    for field in configuration["fields"]:
        identifier = str(field["identifier"])
        if field["type"] == "email":
            pipeline[1]["$project"][f"submission.{identifier}"] = {
                "$cond": {
                    "if": f"$submission.{identifier}",
                    "then": {
                        "email_address": f"$submission.{identifier}",
                        "verified": {
                            "$ifNull": ["$verified", None],
                        },
                    },
                    "else": {
                        "email_address": None,
                        "verified": None,
                    },
                },
            }
        elif field["type"] in ["selection", "text"]:
            pipeline[1]["$project"][f"submission.{identifier}"] = {
                "$ifNull": [f"$submission.{identifier}", None],
            }
    # return empty submissions when survey has no fields
    if not configuration["fields"]:
        pipeline[1]["$project"]["submission"] = {"$literal": {}}
    return pipeline


async def export(submissions, configuration):
    """Export the submissions of a survey in a consistent format."""
    cursor = submissions.aggregate(
        pipeline=_build_aggregation_pipeline(configuration),
        allowDiskUse=True,
    )
    return await cursor.to_list(length=None)
