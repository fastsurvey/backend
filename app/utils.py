import re
import time


def combine(admin_id, survey_name):
    """Build survey identifier from admin_id and survey_name."""
    return f'{admin_id}.{survey_name}'


def isregex(value):
    """Check if a given value is a valid regular expression."""
    try:
        re.compile(value)
        return True
    except:
        return False


def now():
    """Return current unixtime utc timestamp integer."""
    return int(time.time())
