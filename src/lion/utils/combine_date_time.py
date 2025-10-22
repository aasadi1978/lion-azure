from lion.bootstrap.constants import datetime as dt_datetime
from datetime import time as dt_time


def combine_date_time(dt, hhmm):

    hhmm = (f'0000{int(hhmm)}')[-4:]
    h = int(hhmm[:2])
    m = int(hhmm[2:])

    return dt_datetime.combine(dt, dt_time(h, m))