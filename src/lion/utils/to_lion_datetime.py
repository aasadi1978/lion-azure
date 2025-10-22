from lion.bootstrap.constants import datetime as dt_datetime, timedelta


def to_lion_datetime(t='2022-10-04T02:23'):

    strDate = t.replace('T', ' ')

    __dt = dt_datetime.strptime(strDate, "%Y-%m-%d %H:%M")

    return (dt_datetime(__dt.year, __dt.month, __dt.day, __dt.hour, __dt.minute) + timedelta(seconds=1)) - timedelta(seconds=1)