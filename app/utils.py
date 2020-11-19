import re
import time


def identify(configuration):
    """Build survey id from its configuration."""
    admin_name = configuration['admin_name']
    survey_name = configuration['survey_name']
    return f'{admin_name}.{survey_name}'


def isregex(value):
    """Check if a given value is a valid regular expression."""
    try:
        re.compile(value)
        return True
    except:
        return False


def timestamp():
    """Return unixtime utc timestamp integer."""
    return int(time.time())
