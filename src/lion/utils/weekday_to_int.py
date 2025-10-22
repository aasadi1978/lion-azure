from lion.logger.exception_logger import log_exception
def to_daystr(dt):

    try:
        daystr = dt.strftime(
            '%a %H:%M')

        daystr = daystr.replace(
            'Mon', '') if daystr[:3] == 'Mon' else daystr.replace('Tue', '+1')

    except Exception:
        log_exception(popup=False, remarks='_to_daystr failed!')
        return ''

    return daystr