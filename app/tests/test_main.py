import asyncio
import pytest

from fastapi.testclient import TestClient

from .. import main


# create test client
test_client = TestClient(main.app)
# rebind database to testing database
main.db = main.motor_client['async_survey_database_testing']
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
    """Delete all pending and verified entries in the testing collections.

    To avoid deleting real survey entries due to some fault in the database
    remapping, we restrict deletion to the testing email.
    
    """
    yield
    exsync(main.db['pending'].delete_many({'email': 'test123@mytum.de'}))
    exsync(main.db['verified'].delete_many({'email': 'test123@mytum.de'}))


def test_submit_valid_submission(cleanup):
    """Test that submit works with a valid submission for the test survey."""
    submission = {
        'email': 'test123@mytum.de',
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


@pytest.fixture
def setup():
    exsync(main.db['pending'].insert_many([
        {
            'survey': 'test-survey',
            'email': 'test123@mytum.de',
            'properties': {},
            'timestamp': 1590228251,
            'token': 'tomato',
        },
        {
            'survey': 'test-survey',
            'email': 'test123@mytum.de',
            'properties': {},
            'timestamp': 1590228461,
            'token': 'carrot',
        },
    ]))


def test_verify_valid_token(setup, cleanup):
    token = 'tomato'
    response = test_client.get(
        url=f'/test-survey/verify/{token}',
        allow_redirects=False,
    )
    assert response.status_code == 307
    # test if in verified entries
    # test that not in pending entries


# test that verify replaces previously verified entries