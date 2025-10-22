from lion.bootstrap.constants import timedelta
from lion.logger.exception_logger import log_exception
from datetime import datetime
from os import path as os_path


def clean_can_be_executed(mydir, days=30):

    tday = datetime.now()

    try:
        __test_file_path = os_path.join(mydir, '___dir_timestamp_check___.log')

        if not os_path.exists(__test_file_path):
            with open(__test_file_path, 'w') as f:
                dt = tday.strftime('%Y-%m-%d')
                f.write(dt)
        else:
            with open(__test_file_path, 'r') as f:
                dt = f.readline()

        if dt == 'updated':
            with open(__test_file_path, 'w') as f:
                dt = tday.strftime('%Y-%m-%d')
                f.write(dt)

        dt_dt = datetime.strptime(dt, '%Y-%m-%d')

        return dt_dt <= tday - timedelta(days=days)

    except Exception:
        log_exception(
            popup=False, remarks='Could not determine whether clean_can_be_executed!')

    return False