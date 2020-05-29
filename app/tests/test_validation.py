import pytest
import os
import json

from .. import validation


@pytest.fixture
def template(scope='module'):
    folder = os.path.join(os.path.dirname(__file__), '../surveys')
    with open(os.path.join(folder, 'test-survey.json'), 'r') as template:
        return json.load(template)


def test_generate_schema(template):
    """Test that the schema generation function returns the correct result."""
    schema = validation._generate_schema(template)
    assert schema ==  {
        'email': {
            'type': 'string',
            'regex': '^[a-z]{2}[0-9]{2}[a-z]{3}@mytum\.de$',
        },
        'properties': {
            'type': 'dict',
            'schema': {
                'election': {
                    'type': 'Selection',
                    'min_select': 0,
                    'max_select': 2,
                    'schema': {
                        'felix': {
                            'type': 'Option',
                        },
                        'moritz': {
                            'type': 'Option',
                        },
                        'andere': {
                            'type': 'List',
                        },
                    },
                },
                'reason': {
                    'type': 'Text',
                    'min_chars': 10,
                    'max_chars': 100,
                }
            },
        },
    }


valid = [
    {
        'email': 'tt00est@mytum.de',
        'properties': {
            'election': {
                'felix': True,
                'moritz': True,
                'andere': '',
            },
            'reason': 'hello world!',
        }
    },
    {
        'email': 'tt00est@mytum.de',
        'properties': {
            'election': {
                'felix': False,
                'moritz': False,
                'andere': 'Max Mustermann',
            },
            'reason': 'foooooooooooo baaaaaaaaaaaaaaar',
        }
    },
]


def test_validator_passing(template):
    """Check that the generated schema lets some valid submissions pass."""
    validator = validation.create_validator(template)
    for submission in valid:
        assert validator.validate(submission)
