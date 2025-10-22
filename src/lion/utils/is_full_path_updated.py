from lion.orm.time_stamp import TimeStamp
from lion.utils.getmtime import getmtime
from os import path as os_path

def is_full_path_updated(filepath=''):

    __ts = getmtime(filepath)
    filename = os_path.basename(filepath)

    if TimeStamp.get_timestamp(setting_name=filename) != __ts:
        TimeStamp.update(**{filename: __ts})
        return True

    return False