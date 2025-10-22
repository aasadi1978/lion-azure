from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.opt_params import OPT_PARAMS
from lion.orm.drivers_info import DriversInfo
from lion.ui.ui_params import UI_PARAMS
from lion.shift_data.shift_data import UI_SHIFT_DATA


def exclude_double_man_shifts(set_shift_ids_in_scope):
    if set_shift_ids_in_scope:
        return set([d for d in set_shift_ids_in_scope if not DriversInfo.is_doubleman(shift_id=d)])
                                        
    return set_shift_ids_in_scope

def filter_shift_ids_by_user_vehicle(set_shift_ids_in_scope):

    if OPT_PARAMS.USER_VEHICLE_ID and set_shift_ids_in_scope:
        return set([d for d in set_shift_ids_in_scope 
                    if DriversInfo.get_vehicle(shift_id=d) == OPT_PARAMS.USER_VEHICLE_ID])
    
    return set_shift_ids_in_scope

def filter_shift_ids_by_weekdays(set_shift_ids_in_scope):
    """
    Filters shift IDs based on the specified optimization weekdays.
    If `OPT_PARAMS.OPTIMIZATION_WEEKDAYS` is set, this function updates the set of shift IDs in scope
    to include only those that run on the specified weekdays using the `LocalDriversInfo.shift_id_runs_on_weekdays_batch` method.
    Returns:
        set: The filtered set of shift IDs that run on the specified weekdays.
    """
    if OPT_PARAMS.OPTIMIZATION_WEEKDAYS and set_shift_ids_in_scope:
        return set(DriversInfo.shift_id_runs_on_weekdays_batch(shift_ids=list(set_shift_ids_in_scope),
                                                                    weekdays=OPT_PARAMS.OPTIMIZATION_WEEKDAYS))
    
    return set_shift_ids_in_scope

def exclude_fixed_shift_ids(set_shift_ids_in_scope):
    if set_shift_ids_in_scope:
        return set([d for d in set_shift_ids_in_scope
                                                if not UI_SHIFT_DATA.optimal_drivers[d].is_fixed])
    return set_shift_ids_in_scope  
                           
def filter_shift_ids_by_user_vehicle(set_shift_ids_in_scope):
    if set_shift_ids_in_scope:
        return set([d for d in set_shift_ids_in_scope 
                    if DriversInfo.get_vehicle(shift_id=d) == OPT_PARAMS.USER_VEHICLE_ID])
    
    return set_shift_ids_in_scope


def update_excluded_shifts_and_movements():
    """
    Calculates and updates the sets of excluded shift IDs and movements for optimization.
    This function determines which shift IDs and their associated movements should be excluded from the optimization 
    process based on various filters and user-defined parameters. The exclusion criteria include user vehicle preferences, 
    weekday filters, fixed shifts, and optionally double-manned shifts. The function also logs the number of excluded shifts and 
    movements for a specific optimization reporting day.

    Side Effects:

        - Updates OPT_PARAMS.SETOF_EXCLUDED_SHIFT_IDS_FROM_OPT with the set of excluded shift IDs.
        - Updates OPT_PARAMS.SETOF_EXCLUDED_MOVEMENTS_FROM_OPT with the set of excluded movements.
        - Updates OPT_PARAMS.SETOF_SHIFT_IDS_IN_SCOPE with the set of shift IDs considered in scope.
        - Logs information and exceptions using OPT_LOGGER.

    Exceptions:
        - Handles and logs any exceptions that occur during the exclusion process, ensuring that the relevant OPT_PARAMS attributes are reset if an error occurs.
    """

    OPT_LOGGER.log_statusbar('Setting scope ...')

    set_excluded_shift_ids = set()
    set_excluded_movements = set()
    set_shift_ids_in_scope = set()

    try:
        if not UI_PARAMS.LIST_FILTERED_SHIFT_IDS:
            UI_PARAMS.LIST_FILTERED_SHIFT_IDS = list(
                UI_SHIFT_DATA.optimal_drivers.keys())

        if UI_PARAMS.LIST_FILTERED_SHIFT_IDS:
            
            _set_all_shifts = set(
                UI_SHIFT_DATA.optimal_drivers.keys())

            set_shift_ids_in_scope.update(UI_PARAMS.LIST_FILTERED_SHIFT_IDS)

            if 1 in set_shift_ids_in_scope:
                set_shift_ids_in_scope.remove(1)

            if 2 in set_shift_ids_in_scope:
                set_shift_ids_in_scope.remove(2)

            set_shift_ids_in_scope = filter_shift_ids_by_user_vehicle(set_shift_ids_in_scope)
            set_shift_ids_in_scope = filter_shift_ids_by_weekdays(set_shift_ids_in_scope)
            set_shift_ids_in_scope = exclude_fixed_shift_ids(set_shift_ids_in_scope)

            if OPT_PARAMS.EXCL_DBLMAN:
                set_shift_ids_in_scope = exclude_double_man_shifts(set_shift_ids_in_scope)

            if set_shift_ids_in_scope:
                set_excluded_shift_ids.update([d for d in _set_all_shifts
                                                    if d not in set_shift_ids_in_scope])

            if 1 in set_excluded_shift_ids:
                set_excluded_shift_ids.remove(1)

            if 2 in set_excluded_shift_ids:
                set_excluded_shift_ids.remove(2)

            for shiftid in set_excluded_shift_ids:
                set_excluded_movements.update(
                    UI_SHIFT_DATA.optimal_drivers[shiftid]['list_movements'])

            _set_excluded_shift_ids_single_day = set([d for d in set_excluded_shift_ids
                                                        if DriversInfo.shift_id_runs_on_weekday(
                                                            shift_id=d, weekday=OPT_PARAMS.OPTIMIZATION_REP_DAY)])

            __set_excluded_movements_single_day = set()
            for t in _set_excluded_shift_ids_single_day:
                __set_excluded_movements_single_day.update(
                    UI_SHIFT_DATA.optimal_drivers[t][
                        'list_movements'])

            __n_excl_shifts = len(
                _set_excluded_shift_ids_single_day)

            __n_excl_movs = len(__set_excluded_movements_single_day)

            OPT_LOGGER.log_info(
                message=f'There are {__n_excl_shifts} drivers/{__n_excl_movs} loaded and repos movs excluded from lion.optimization based on {OPT_PARAMS.OPTIMIZATION_REP_DAY} filter!')

    except Exception:

        _err = OPT_LOGGER.log_exception(
            popup=True, remarks='getting excluded drivers was not done successfully')

        set_excluded_shift_ids = set()
        set_excluded_movements = set()

        OPT_LOGGER.log_info(
            message=f'No driver was excluded from lion.optimization! {_err}')
        
        return

    OPT_PARAMS.SETOF_EXCLUDED_SHIFT_IDS_FROM_OPT = set_excluded_shift_ids
    OPT_PARAMS.SETOF_EXCLUDED_MOVEMENTS_FROM_OPT = set_excluded_movements
    OPT_PARAMS.SETOF_SHIFT_IDS_IN_SCOPE = set_shift_ids_in_scope
