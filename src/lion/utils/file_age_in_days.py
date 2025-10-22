from lion.bootstrap.constants import datetime as dt_datetime, timedelta
from pytz import timezone


from os import path as os_path


def file_age_in_days(filepath):

    def __utc2dt(utc):
        return dt_datetime.fromtimestamp(utc/1000, timezone("UTC"))

    try:

        t = os_path.getmtime(filepath)
        file_time_stamp = __utc2dt(t * 1000)

        file_time_stamp = file_time_stamp.replace(tzinfo=None)

        __total_seconds = (dt_datetime.now() - file_time_stamp).total_seconds()

        return timedelta(seconds=__total_seconds).days

    except Exception:
        return 0