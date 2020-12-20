import re
import time


def combine(admin_name, survey_name):
    """Build unique survey identifier from admin_name and survey_name."""
    return f'{admin_name}.{survey_name}'


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
