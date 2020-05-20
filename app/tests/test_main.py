import asyncio
import pytest

from fastapi.testclient import TestClient

from .. import main


# create test client
test_client = TestClient(main.app)
# rebind database to testing database
main.db = main.client['async_survey_database_testing']
# rebind surveys with new testing database
main.surveys = main.create_surveys(main.db)


def test_db_rebinding():
    """Test if the database is correctly remapped to the testing database."""
    assert main.db.name == 'async_survey_database_testing'


def test_status_passing():
    """Test that status function returns that all services are operational."""
    response = test_client.get('/')
    assert response.status_code == 200
    assert response.json() == {'status': 'all services operational'}


def exsync(code):
    """Helper function for executing async code synchronously in sync code."""
    return asyncio.get_event_loop().run_until_complete(code)


@pytest.fixture
def cleanup():
    yield
    exsync(main.db['pending'].delete_one({'email': '1234567@mytum.de'}))


def test_submit_valid_submission(cleanup):
    """Test that submit works with a valid submission for the test survey."""
    submission = {
        'email': '1234567@mytum.de',
        'properties': {
            'election': {
                'felix': True,
                'moritz': True,
                'andere': '',
            },
            'reason': '',
        },
    }
    response = test_client.post(url='/test-survey/submit', json=submission)
    assert response.status_code == 200
    entry = exsync(main.db['pending'].find_one(projection={'_id': False}))
    keys = {'survey', 'email', 'properties', 'timestamp', 'token'}
    assert set(entry.keys()) == keys
    assert entry['email'] == submission['email']
    assert entry['properties'] == submission['properties']
    assert entry['survey'] == 'test-survey'
