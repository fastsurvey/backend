from .. import main


# rebind database to testing database
main.db = main.client['async_survey_database_testing']
# rebind surveys with new testing database
main.surveys = main.create_surveys(main.db)


def test_db_rebinding():
    """Test if the database is correctly remapped to the testing database."""
    assert main.db.name == 'async_survey_database_testing'
