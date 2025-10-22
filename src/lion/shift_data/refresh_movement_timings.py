
from datetime import timedelta
from lion.orm.location import Location
from lion.shift_data.exceptions import EXCEPTION_HANDLER
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.logger.exception_logger import log_exception


def refresh(list_movements=[]):

    try:

        if len(list_movements) >= 2:

            dct_footprint = Location.to_dict()

            __m_pairs = [(list_movements[i], list_movements[i+1])
                            for i in range(len(list_movements)-1)]

            while __m_pairs:

                __m1, __m2 = __m_pairs.pop(0)

                __turnaround_drive = dct_footprint[UI_MOVEMENTS.dict_all_movements[__m1]
                                                            ['To']]['chgover_driving_min']

                __turnaround_non_drive = dct_footprint[UI_MOVEMENTS.dict_all_movements[__m1]
                                                                ['To']]['chgover_non_driving_min']

                __turnaround_time = __turnaround_non_drive + __turnaround_drive

                __delta = int(0.5 + (UI_MOVEMENTS.dict_all_movements[
                    __m2]['DepDateTime'] - UI_MOVEMENTS.dict_all_movements[__m1][
                    'ArrDateTime']).total_seconds()/60)

                if __delta < __turnaround_time:

                    __new_dep_dt = UI_MOVEMENTS.dict_all_movements[__m1]['ArrDateTime'] + timedelta(
                        minutes=__turnaround_time)

                    UI_MOVEMENTS.update_movement_for_new_deptime(
                        __m2, __new_dep_dt)

    except Exception:
        EXCEPTION_HANDLER.update(log_exception(popup=False))