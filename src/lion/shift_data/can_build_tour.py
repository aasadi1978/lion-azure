from datetime import timedelta
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.logger.exception_logger import log_exception


def validate_movement_tour(list_movs=[]):

        n_movs = len(list_movs)
        if n_movs < 2:
            return True

        for m in list_movs:
            UI_SHIFT_DATA.dict_all_movements[m]['From']

        try:
            __dur = int((UI_SHIFT_DATA.dict_all_movements[list_movs[-1]]['ArrDateTime'] -
                         UI_SHIFT_DATA.dict_all_movements[list_movs[0]]['DepDateTime']).total_seconds()/60) + 60

            if __dur > 720:
                return False

            __m_pairs = [(list_movs[i], list_movs[i+1])
                         for i in range(n_movs-1)]

            list_movs = []
            while __m_pairs:

                m1, m2 = __m_pairs.pop(0)
                __dest_m1 = UI_SHIFT_DATA.dict_all_movements[m1]['To']
                __orig_m2 = UI_SHIFT_DATA.dict_all_movements[m2]['From']

                if __dest_m1 == __orig_m2:
                    if (UI_SHIFT_DATA.dict_all_movements[m2]['DepDateTime'] -
                            UI_SHIFT_DATA.dict_all_movements[m1]['ArrDateTime']).total_seconds()/60 < 20:

                        return False

                else:
                    __interim_m_driving_time = UI_RUNTIMES_MILEAGES.get_movement_driving_time(
                        orig=__dest_m1, dest=__orig_m2, vehicle=UI_SHIFT_DATA.dict_all_movements[m2]['VehicleType'], apply_utc=1)

                    __dur = __dur + __interim_m_driving_time
                    if __dur > 720:
                        return False

                    __arr_dt = UI_SHIFT_DATA.dict_all_movements[m1]['ArrDateTime'] + timedelta(
                        minutes=__interim_m_driving_time + 20)

                    if (__arr_dt + timedelta(minutes=20)) > (
                            UI_SHIFT_DATA.dict_all_movements[m2]['DepDateTime']):

                        return False

            return True

        except Exception:
            log_exception(
                popup=False, remarks='Initial tour check failed!')

            return False