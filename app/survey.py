import pymongo.errors

import app.aggregation as aggregation
import app.database as database
import app.errors as errors
import app.exportation as exportation


def submissions_collection(configuration):
    """Build link to submission collection from survey configuration."""
    identifier = configuration["_id"]
    return database.database[f"surveys.{identifier}.submissions"]


async def read(username, survey_name):
    """Return the survey configuration corresponding to the user's survey."""
    configuration = await database.database["configurations"].find_one(
        filter={"username": username, "survey_name": survey_name},
        projection={"username": False},
    )
    if configuration is None:
        raise errors.SurveyNotFoundError()
    return configuration


async def read_multiple(username):
    """Return a list of the user's survey configurations."""
    cursor = database.database["configurations"].find(
        filter={"username": username},
        projection={"_id": False, "username": False},
    )
    return await cursor.to_list(None)


async def create(username, configuration):
    """Create a new survey configuration in the database."""
    identifiers = {field["identifier"] for field in configuration["fields"]}
    if identifiers != set(range(len(configuration["fields"]))):
        raise errors.InvalidSyntaxError()
    try:
        await database.database["configurations"].insert_one(
            document={
                "username": username,
                "next_identifier": max(identifiers) + 1 if identifiers else 0,
                **configuration,
            },
        )
    except pymongo.errors.DuplicateKeyError as error:
        index = str(error).split()[7]
        if index == "username_survey_name_unique_index":
            raise errors.SurveyNameAlreadyTakenError()
        else:
            raise errors.InternalServerError()


async def update(username, survey_name, update):
    """Update a survey configuration in the database.

    Survey updates are possible even if the survey already has submissions.
    This works by assigning each field an identifier that is unique over the
    lifetime of the survey. During updates, new fields are assigned a new
    identifier. Changes to individual fields do not affect their identifier.
    Changes to the field type necessitate a new identifier.

    The configuration includes the survey_name despite it already being
    specified in the route. We do this in order to enable changing the
    survey_name.

    """
    configuration = await read(username, survey_name)

    def identifiers(configuration):
        return {field["identifier"] for field in configuration["fields"]}

    # check that fields with unchanged identifier have the same field type
    for x in update["fields"]:
        for y in configuration["fields"]:
            if x["identifier"] == y["identifier"] and x["type"] != y["type"]:
                raise errors.InvalidSyntaxError()

    # check that new fields are numbered in ascending order
    new = identifiers(update) - identifiers(configuration)
    for i, e in enumerate(sorted(new)):
        if e != configuration["next_identifier"] + i:
            raise errors.InvalidSyntaxError()

    # write changes to database
    try:
        res = await database.database["configurations"].replace_one(
            filter={
                "_id": configuration["_id"],
                # this ensures that even when the configuration changed
                # between read and write, that only valid updates are written
                "next_identifier": configuration["next_identifier"],
            },
            replacement={
                "username": username,
                "next_identifier": max(
                    [
                        max(identifiers(update)) + 1 if identifiers(update) else 0,
                        configuration["next_identifier"],
                    ]
                ),
                **update,
            },
        )
    except pymongo.errors.DuplicateKeyError as error:
        index = str(error).split()[7]
        if index == "username_survey_name_unique_index":
            raise errors.SurveyNameAlreadyTakenError()
        else:
            raise errors.InternalServerError()
    if res.matched_count == 0:
        raise errors.InvalidSyntaxError()


async def reset(username, survey_name):
    """Delete all submission data but keep the survey configuration."""
    configuration = await read(username, survey_name)
    submissions = submissions_collection(configuration)
    await submissions.drop()


async def delete(username, survey_name):
    """Delete the survey and all its data from the database."""
    configuration = await read(username, survey_name)
    submissions = submissions_collection(configuration)
    async with await database.client.start_session() as session:
        async with session.start_transaction():
            await database.database["configurations"].delete_one(
                filter={"_id": configuration["_id"]},
            )
            await submissions.drop()


async def aggregate(username, survey_name):
    """Query the survey submissions and return aggregated results."""
    configuration = await read(username, survey_name)
    submissions = submissions_collection(configuration)
    return await aggregation.aggregate(submissions, configuration)


async def export(username, survey_name):
    """Export the submissions of a survey in a consistent format."""
    configuration = await read(username, survey_name)
    submissions = submissions_collection(configuration)
    return await exportation.export(submissions, configuration)
