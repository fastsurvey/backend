import time
import datetime as dt


def timestamp():
    """Return current UTC time as unixtime integer."""
    return int(time.time())


def now():
    """Return current UTC time as datetime object."""
    return dt.datetime.now(dt.timezone.utc)
