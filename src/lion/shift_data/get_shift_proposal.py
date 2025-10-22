from collections import OrderedDict
from datetime import datetime
from lion.driver_loc.location_finder import LocationFinder
from lion.logger.status_logger import log_message
from lion.orm.drivers_info import DriversInfo
from pandas import DataFrame
from lion.movement import sort_list_movements
from lion.shift_data.can_build_tour import validate_movement_tour
from lion.shift_data.exceptions import EXCEPTION_HANDLER
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.utils.elapsed_time import ELAPSED_TIME
from os import path as os_path
from lion.config.paths import LION_LOGS_PATH
from lion.logger.exception_logger import log_exception
from lion.utils.popup_notifier import show_error
from lion.xl.write_excel import write_excel as xlwriter
from lion.shift_data.build_tours import build as _build_tours


def __evaluate_shifts_for_a_movement(set_movement_shift_suggested_pairs,
                                     movement_id, 
                                     shifts2review=[]):

    try:

        if not shifts2review:
            return

        __loc_string = UI_SHIFT_DATA.dict_all_movements.get(
            movement_id, {}).get('loc_string', '')

        while shifts2review:

            shift_id = shifts2review.pop()
            __list_of_movements = []
            __list_of_sorted_movements = []
            __dct_tour = {}

            try:

                sname = UI_SHIFT_DATA.optimal_drivers.get(
                    shift_id, {}).get('driver', '')

                __list_of_movements.extend(UI_SHIFT_DATA.optimal_drivers.get(
                    shift_id, {}).get('list_loaded_movements', []))

                if movement_id not in __list_of_movements:
                    __list_of_movements.append(movement_id)

                __new_m_vehicle = UI_SHIFT_DATA.dict_all_movements.get(
                    movement_id, {}).get('VehicleType', 1)

                __shift_vehicle = UI_SHIFT_DATA.optimal_drivers[shift_id].get(
                    'vehicle', 1)

                is_double_man = UI_SHIFT_DATA.optimal_drivers[shift_id].get(
                    'double_man', False)

                if __shift_vehicle == __new_m_vehicle:

                    __list_of_sorted_movements, _ = sort_list_movements.sorted_movements(
                        list_of_movs=__list_of_movements)

                    if __list_of_sorted_movements and validate_movement_tour(list_movs=__list_of_sorted_movements):

                        __dct_tour = _build_tours(
                            shift_id=shift_id, 
                            list_of_sorted_loaded_movements=__list_of_sorted_movements,
                            is_doubleman=is_double_man,
                            report_exception=False)

                        if __dct_tour:
                            set_movement_shift_suggested_pairs.update([(__loc_string, sname)])

            except Exception:
                log_exception(
                    remarks=f'Evaluating {sname} failed!', popup=False)

    except Exception:
        __exception_message = log_exception(
            remarks='Searching for shift failed!', popup=False)

        EXCEPTION_HANDLER.update(__exception_message)

    return

def get_shift_proposals(shifts2review=[], list_m=[], weekday=''):

    local_exceptions = EXCEPTION_HANDLER.reset()
    dct_drivers = DriversInfo.to_dict()
    local_notifications = ''

    ELAPSED_TIME.reset()

    try:
        logger_file = os_path.join(
            LION_LOGS_PATH, 'movement-2-shift-assignment.log')

        with open(logger_file, 'w') as __tmpFile:
            __tmpFile.writelines('\n' + local_notifications + '\n')

        dct_m_shifts = {}
        set_movement_shift_suggested_pairs = set()

        loc_finder = LocationFinder().dct_close_by_driver_locs

        if not loc_finder:
            raise ValueError(
                'dct_close_by_driver_locs dict is empty!')

        if not list_m:

            list_m = list(UI_SHIFT_DATA.dct_unplanned_movements)
            log_message(
                f"We found {len(list_m)} movements to assign: {';'.join([str(x) for x in list_m[:5]])}")

        __set_dump_area_movs = set(
            UI_SHIFT_DATA.set_movement_dump_movements)

        for m in __set_dump_area_movs:
            if m not in list_m:
                list_m.append(m)
        
        if not list_m:
            show_error(message='No movement was found to evaluate!')
            return


        __list_unfixed_shifts = [d for d in set(
            UI_SHIFT_DATA.optimal_drivers) if not UI_SHIFT_DATA.optimal_drivers[d]['is_fixed']]

        if weekday != '':
            __list_unfixed_shifts = [d for d in __list_unfixed_shifts if
                                        DriversInfo.shift_id_runs_on_weekday(shift_id=d, weekday=weekday)]

        if shifts2review:
            shifts2review = [
                t for t in shifts2review if t in __list_unfixed_shifts]
        else:
            shifts2review = __list_unfixed_shifts

        del __list_unfixed_shifts

        if loc_finder:

            for m in list_m:

                __loc_from = UI_SHIFT_DATA.dict_all_movements[m]['From']
                __loc_to = UI_SHIFT_DATA.dict_all_movements[m]['To']

                __list_locs = loc_finder.get(
                    __loc_from, [])  # [:10]

                __shifts = []
                for __loc in __list_locs:
                    __shifts.extend([d for d in shifts2review if dct_drivers.get(
                        d, {}).get('loc', '') == __loc])

                __shifts = list(OrderedDict.fromkeys(__shifts))

                dct_m_shifts[m] = [
                    d for d in __shifts if d in shifts2review]

                del __loc_from, __loc_to, __shifts, __list_locs

    except Exception:
        local_exceptions = \
            f"{local_exceptions}\n{log_exception(
                popup=False, remarks='preprocessing - evaluate_shifts_for_movements failed!')}"
        
    try:
        _n_movs = len(list_m)
        ctr = 0
        _t_start = datetime.now()

        for m_id in list_m:
            ctr += 1

            __evaluate_shifts_for_a_movement(
                set_movement_shift_suggested_pairs=set_movement_shift_suggested_pairs,
                movement_id=m_id, shifts2review=dct_m_shifts.get(m_id, []))

            scnds = int((datetime.now() - _t_start).total_seconds())

            with open(logger_file, 'a') as __tmpFile:
                __tmpFile.writelines(
                    f'\nThe movement {ctr}/{_n_movs} has been processed. Seconds elapsed: {scnds}')

        if set_movement_shift_suggested_pairs:

            __df_shifts = DataFrame(set_movement_shift_suggested_pairs, columns=[
                                    'loc_string', 'Shift'])

            __df_shifts.sort_values(by=['loc_string'], inplace=True)

            xlpath = os_path.join(
                LION_LOGS_PATH, f'shift_proposals-{UI_SHIFT_DATA.weekday}.xlsx')

            
            xlwriter(df=__df_shifts.copy(),
                        sheetname='Shifts',  xlpath=xlpath, echo=False)

            local_notifications = f'There are {__df_shifts.shape[0]} movement-shift proposal(s) in\n{xlpath}'

        else:
            local_notifications = 'No proposed shift has been found!'

    except Exception:

        __exception_message = log_exception(
            remarks=f'evaluate_shifts_for_movements failed!', popup=False)

        local_exceptions = f"{local_exceptions}\n{__exception_message}"
        EXCEPTION_HANDLER.update(local_exceptions)

        with open(logger_file, 'a') as __tmpFile:
            __tmpFile.writelines('\n' + local_notifications + '\n')

    with open(logger_file, 'a') as __tmpFile:
        __tmpFile.writelines(
            '\n' + f"Processing time for {len(list_m)} movements: {ELAPSED_TIME.collapsed_time()}" + '\n')
