import re


def identify(configuration):
    """Build survey id from its configuration."""
    admin_name = configuration['admin_name']
    survey_name = configuration['survey_name']
    return f'{admin_name}.{survey_name}'


def isregex(s):
    """Check if a given string is a valid regular expression."""
    try:
        re.compile(s)
        return True
    except re.error:
        return False
