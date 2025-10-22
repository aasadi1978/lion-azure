from datetime import datetime, timedelta
from lion.bootstrap.constants import LION_DATES
from lion.optimization.optimization_logger import OPT_LOGGER

def get_datetime(depday, deptime, schedule_day='Mon'):

    try:

        time_obj = datetime.strptime(
            f'0000{deptime}'[-4:], "%H%M").time()

        dep_date_time = datetime.combine(
            LION_DATES[schedule_day], time_obj)

        dep_date_time = dep_date_time + timedelta(days=depday)

        return dep_date_time

    except Exception as e:
        OPT_LOGGER.log_exception(f"date time could not be built: {str(e)}")

    return None