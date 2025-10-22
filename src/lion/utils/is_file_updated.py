from os import path
from lion.orm.time_stamp import TimeStamp
from lion.logger.exception_logger import log_exception
from lion.utils.get_file_ts import get_file_ts


def is_file_updated(filename, Path=None) -> bool:

    try:
        
        filename_basename = path.basename(filename)
        filename_current_timestamp = get_file_ts(filename=filename, Path=Path)

        if filename_current_timestamp and (
            TimeStamp.get_timestamp(setting_name=filename_basename) != filename_current_timestamp):
            TimeStamp.update(**{filename_basename: filename_current_timestamp})
            return True

    except Exception:
        log_exception(popup=False)

    return False