import time
import random


def combine(username, survey_name):
    """Build unique survey identifier from username and survey_name."""
    return f'{username}.{survey_name}'


def identify(username, configuration):
    """Build unique survey identifier from username and configuration."""
    return combine(username, configuration['survey_name'])


def now():
    """Return current unixtime utc timestamp integer."""
    return int(time.time())


def identifier():
    """Generate a random string useful as identifier."""
    return f'{random.randrange(16**16):016x}'
