from lion.bootstrap.constants import LOC_STRING_SEPERATOR
from lion.orm.changeover import Changeover
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.logger.exception_logger import log_exception


def get_changeover_shiftids(loc_string=''):

    try:

        if len(loc_string.split(LOC_STRING_SEPERATOR)) >= 4:

            movs = Changeover.get_legs(loc_string=loc_string)
            if movs:
                sids = [
                    UI_SHIFT_DATA.dict_all_movements[m].shift_id for m in movs]

                return sids

    except Exception:
        log_exception(
            popup=False, remarks=f"Could not get shifts for {loc_string}")

    return []