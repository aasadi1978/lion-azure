from collections import defaultdict
from lion.optimization.opt_params import OPT_PARAMS
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.utils.safe_copy import secure_copy
from lion.optimization.optimization_logger import OPT_LOGGER


def calculate_dct_driver_locs_per_lane() -> dict:
    """
    Calculates and updates the mapping of driver locations per lane for planned loaded movements.
    This function processes planned loaded movements and associates driver locations with each lane and linehaul ID.
    It also handles dummy driver locations for optimal driver tours. The results are stored in the global
    OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE dictionary.
    Args:
        clear_cache (bool, optional): If True, clears the existing driver locations per lane cache before calculation.
            Defaults to False.
    Returns:
        bool: True if the calculation and update were successful, False otherwise.
    Side Effects:
        - Updates OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE with the new mapping.
        - Logs exceptions using OPT_LOGGER if any errors occur during processing.

    The dictionary DCT_DRIVER_LOCS_PER_LANE will be used as a guide to cluster movements around driver locations
    """

    dct_driver_locs_per_lane  = defaultdict(set)

    OPT_LOGGER.log_statusbar(
        message='Calculating driver locations per lane...')
    
    try:

        list_planned_loaded_movements = list(
            UI_SHIFT_DATA.set_planned_loaded_movements)

        dct_loaded_movements = {
            m: UI_SHIFT_DATA.dict_all_movements[m] for m in list_planned_loaded_movements}

        for m in list_planned_loaded_movements:

            driver_loc = dct_loaded_movements[m]['shift'].split('.')[0]
            if driver_loc not in OPT_PARAMS.EXCLUDED_LOCS:

                dct_loaded_movements[m].update({
                    'linehaul_id': '.'.join([dct_loaded_movements[m]['From'],
                                            dct_loaded_movements[m]['To'],
                                            dct_loaded_movements[m]['DepDateTime'].strftime('%H%M')]),

                    'Lane': '.'.join([dct_loaded_movements[m]['From'], dct_loaded_movements[m]['To']]),
                    'DriverLoc': driver_loc
                })

        while list_planned_loaded_movements:

            try:
                dct_m = dct_loaded_movements.get(
                    list_planned_loaded_movements.pop(), {})

                dloc = dct_m.get('DriverLoc', None)

                if dloc:

                    dct_driver_locs_per_lane.setdefault(
                        dct_m.linehaul_id, set()).add(dloc)

                    dct_driver_locs_per_lane.setdefault(
                        dct_m['Lane'], set()).add(dloc)

                    del dct_m

            except Exception:
                OPT_LOGGER.log_exception(popup=False)

        cntr = 1
        for dct_tour in UI_SHIFT_DATA.optimal_drivers.values():

            tour_loc_from = dct_tour['tour_loc_from']
            list_loaded = dct_tour['list_loaded_movements']

            for m in list_loaded:
                lane = '.'.join(
                    [dct_loaded_movements[m]['From'], dct_loaded_movements[m]['To']])
                dct_driver_locs_per_lane.setdefault(
                    lane, set()).add(f"{tour_loc_from}.DummyLoc.{cntr}")

            cntr += 1

        del dct_loaded_movements

    except Exception:
        OPT_LOGGER.log_exception(
            popup=False, remarks='Driver location per lane failed!')
        
        return False
    
    OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE = secure_copy(dct_driver_locs_per_lane)

    return True