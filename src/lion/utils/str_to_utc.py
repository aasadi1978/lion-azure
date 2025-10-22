from lion.bootstrap.constants import datetime as dt_datetime


from datetime import timezone as dt_timezone


def str2UTC(strDate, frmt="%Y-%m-%d %H:%M"):
    dt = dt_datetime.strptime(strDate, frmt)
    timestamp = dt.replace(tzinfo=dt_timezone.utc).timestamp()

    return timestamp * 1000