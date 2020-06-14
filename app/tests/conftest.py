import pytest

from motor.motor_asyncio import AsyncIOMotorClient

from .. import main
from .. import survey


@pytest.fixture(scope='function', autouse=True)
def setup(event_loop):
    """Reconfigure motor client's event loop and database before a test."""
    # rebind event loop of the motor client
    main.motor_client = AsyncIOMotorClient(main.MDBCSTR, io_loop=event_loop)
    # rebind database to new motor client
    main.database = main.motor_client['main']
    # rebind survey manager
    main.manager = survey.SurveyManager(main.database)
