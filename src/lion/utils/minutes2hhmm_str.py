from humanfriendly import format_timespan
from lion.bootstrap.constants import timedelta
from lion.logger.exception_logger import log_exception


def minutes2hhmm_str(m):
    try:
        return format_timespan(timedelta(minutes=m))
    except Exception:
        log_exception(False)
        return 'No time due to ERR'