from collections import defaultdict
from lion.ui.ui_params import UI_PARAMS
from lion.orm.drivers_info import DriversInfo
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.logger.exception_logger import log_exception


def splitted_shifts_fixed_unfixed():

    try:

        dct_loc_unfixed_subco_drivers = defaultdict(set)
        dct_loc_unfixed_employed_drivers = defaultdict(set)

        dct_loc_fixed_subco_drivers = defaultdict(set)
        dct_loc_fixed_employed_drivers = defaultdict(set)

        set_drivers = list(UI_SHIFT_DATA.optimal_drivers)

        if set_drivers:
            if UI_PARAMS.FILTERING_WKDAYS:
                wkday = UI_PARAMS.FILTERING_WKDAYS[0]
                set_drivers = [d for d in set_drivers if DriversInfo.shift_id_runs_on_weekday(
                    shift_id=d, weekday=wkday)]

            dct_drivers = DriversInfo.to_sub_dict(shift_ids=list(set_drivers))

            set_employed = set([d for d in set_drivers if
                                    dct_drivers.get(d, {}).get('operator', '').lower() == 'fedex express'])


            set_fixed_shifts = set([d for d in dct_drivers 
                                          if UI_SHIFT_DATA.optimal_drivers[d].is_fixed])

            set_fixed_employed_tours = set(
                [d for d in set_employed if d in set_fixed_shifts])

            set_unfixed_employed_tours = set(
                [d for d in set_employed if d not in set_fixed_shifts])

            set_subco = set(
                [d for d in set_drivers if d not in set_employed])

            set_fixed_subco_tours = set(
                [d for d in set_subco if d in set_fixed_shifts])

            set_unfixed_subco_tours = set(
                [d for d in set_subco if d not in set_fixed_shifts])

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

        log_exception(
            popup=False, remarks='Dumping drivers per loc failed!')

    return dict(dct_loc_unfixed_employed_drivers), dict(dct_loc_fixed_employed_drivers), \
        dict(dct_loc_fixed_subco_drivers), dict(
            dct_loc_unfixed_subco_drivers)