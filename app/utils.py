import time


def combine(username, survey_name):
    """Build unique survey identifier from username and survey_name."""
    return f'{username}.{survey_name}'


def identify(configuration):
    """Build unique survey identifier from username and survey_name."""
    return combine(configuration['username'], configuration['survey_name'])


def now():
    """Return current unixtime utc timestamp integer."""
    return int(time.time())
