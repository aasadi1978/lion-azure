from collections import defaultdict
from lion.optimization.opt_params import OPT_PARAMS
from lion.orm.drivers_info import DriversInfo
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.optimization.optimization_logger import OPT_LOGGER


def dump_dct_drivers_per_location():
    """
    Categorizes and returns drivers per location based on employment type and fixed/unfixed status.
    This function processes the optimal drivers from `UI_SHIFT_DATA`, filters them according to weekday and operator,
    and splits them into four categories for each location:
        - Unfixed employed drivers
        - Fixed employed drivers
        - Fixed subcontractor drivers
        - Unfixed subcontractor drivers
    Returns:
        tuple: A tuple containing four dictionaries:
            - dict_loc_unfixed_employed_drivers (dict): {location: set of unfixed employed driver shift IDs}
            - dict_loc_fixed_employed_drivers (dict): {location: set of fixed employed driver shift IDs}
            - dict_loc_fixed_subco_drivers (dict): {location: set of fixed subcontractor driver shift IDs}
            - dict_loc_unfixed_subco_drivers (dict): {location: set of unfixed subcontractor driver shift IDs}
    Exceptions:
        On exception, logs the error and returns empty dictionaries for all four categories.
    """

    try:

        dct_loc_unfixed_subco_drivers = defaultdict(set)
        dct_loc_unfixed_employed_drivers = defaultdict(set)

        dct_loc_fixed_subco_drivers = defaultdict(set)
        dct_loc_fixed_employed_drivers = defaultdict(set)

        set_drivers = list(UI_SHIFT_DATA.optimal_drivers)

        if set_drivers:

            if OPT_PARAMS.FILTERING_WKDAYS:
                
                wkday = OPT_PARAMS.FILTERING_WKDAYS[0]
                set_drivers = [d for d in set_drivers if DriversInfo.shift_id_runs_on_weekday(
                    shift_id=d, weekday=wkday)]

            dct_drivers = DriversInfo.to_sub_dict(shift_ids=list(set_drivers))

            set_employed = set([d for d in set_drivers if
                                    dct_drivers.get(d, {}).get('operator', '').lower() == 'fedex express'])

            set_fixed_employed_tours = set(
                [d for d in set_employed if d in OPT_PARAMS.SETOF_EXCLUDED_SHIFT_IDS_FROM_OPT])

            set_unfixed_employed_tours = set(
                [d for d in set_employed if d not in OPT_PARAMS.SETOF_EXCLUDED_SHIFT_IDS_FROM_OPT])

            set_subco = set(
                [d for d in set_drivers if d not in set_employed])

            set_fixed_subco_tours = set(
                [d for d in set_subco if d in OPT_PARAMS.SETOF_EXCLUDED_SHIFT_IDS_FROM_OPT])

            set_unfixed_subco_tours = set(
                [d for d in set_subco if d not in OPT_PARAMS.SETOF_EXCLUDED_SHIFT_IDS_FROM_OPT])

            list_driver_locs = list(
                set([v['loc'] for v in dct_drivers.values()]))

            del set_drivers, set_employed, set_subco

            while list_driver_locs:

                lc = list_driver_locs.pop()

                dct_loc_unfixed_employed_drivers[lc].update([d for d in set_unfixed_employed_tours if
                                                                dct_drivers.get(d, {}).get('loc', '') == lc])

                dct_loc_fixed_employed_drivers[lc].update([d for d in set_fixed_employed_tours if
                                                                dct_drivers.get(d, {}).get('loc', '') == lc])

                dct_loc_fixed_subco_drivers[lc].update([d for d in set_fixed_subco_tours if
                                                            dct_drivers.get(d, {}).get('loc', '') == lc])

                dct_loc_unfixed_subco_drivers[lc].update([d for d in set_unfixed_subco_tours if
                                                            dct_drivers.get(d, {}).get('loc', '') == lc])

            del set_fixed_subco_tours, set_unfixed_subco_tours, \
                set_unfixed_employed_tours, set_fixed_employed_tours

    except Exception:
    
        dct_loc_unfixed_subco_drivers = defaultdict(set)
        dct_loc_unfixed_employed_drivers = defaultdict(set)
        dct_loc_fixed_subco_drivers = defaultdict(set)
        dct_loc_fixed_employed_drivers = defaultdict(set)

        OPT_LOGGER.log_exception(
            popup=False, remarks='Dumping drivers per loc failed!')

    return dict(dct_loc_unfixed_employed_drivers), dict(dct_loc_fixed_employed_drivers), \
        dict(dct_loc_fixed_subco_drivers), dict(
            dct_loc_unfixed_subco_drivers)