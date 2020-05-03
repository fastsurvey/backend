
from datetime import datetime, timedelta, timezone


def get_current_time(offset_seconds=0, offset_minutes=0, offset_hours=0, offset_days=0):
    current_time = datetime.now(timezone(timedelta(hours=2)))
    current_time += timedelta(seconds=offset_seconds,
                              minutes=offset_minutes,
                              hours=offset_hours,
                              days=offset_days)
    return current_time


def datetime_to_string(datetime_object):
    return datetime_object.strftime("%d.%m.%y, %H:%M")
