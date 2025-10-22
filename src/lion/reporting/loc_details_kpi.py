from lion.logger.exception_logger import log_exception
from lion.logger.status_logger import log_message
from lion.orm.drivers_info import DriversInfo
from pandas import DataFrame
from collections import defaultdict
from lion.shift_data.shift_data import UI_SHIFT_DATA


def calculate_location_kpis(weekday='Mon'):

    try:

        __dct_loc_fixed_drivers = defaultdict(set)
        __dct_loc_drivers = defaultdict(set)

        if not UI_SHIFT_DATA.optimal_drivers:
            print("No optimal drivers found for KPI's.")
            return DataFrame()

        __set_drivers = set(UI_SHIFT_DATA.optimal_drivers)

        if 1 in __set_drivers:
            __set_drivers.remove(1)

        if 2 in __set_drivers:
            __set_drivers.remove(2)

        __set_drivers = [d for d in __set_drivers if DriversInfo.shift_id_runs_on_weekday(
            shift_id=d, weekday=weekday)]

        dct_drivers = DriversInfo.to_sub_dict(shift_ids=__set_drivers)

        __dct_employed_driver_per_loc = DriversInfo.get_employed_drivers_per_loc(
            shift_ids=__set_drivers)

        __fixed_tours = set(
            d for d in __set_drivers if UI_SHIFT_DATA.optimal_drivers[d]['is_fixed'])

        __set_driver_locs = set(
            [dct_drivers[d]['loc'] for d in __set_drivers])

        for lc in __set_driver_locs:
            __dct_loc_fixed_drivers[lc].update([d for d, v in
                                                dct_drivers.items() if v['loc'] == lc and d in __fixed_tours])

        __set_drivers = [
            d for d in __set_drivers if d not in __fixed_tours]

        for lc in __set_driver_locs:
            __dct_loc_drivers[lc].update([d for d, v in
                                          dct_drivers.items() if v['loc'] == lc])

        __df_locs = DataFrame(
            list(__set_driver_locs), columns=['loc_code'])

        __df_locs['UnFixed'] = __df_locs.loc_code.apply(
            lambda x: len(__dct_loc_drivers.get(x, [])))

        __df_locs['Fixed'] = __df_locs.loc_code.apply(
            lambda x: len(__dct_loc_fixed_drivers.get(x, [])))

        __df_locs['Employed'] = __df_locs.loc_code.apply(
            lambda x: __dct_employed_driver_per_loc.get(x, 0))

        __df_locs['TotalDrivers'] = __df_locs.apply(
            lambda x: x['Fixed'] + x['UnFixed'], axis=1)

        __df_locs['Subco'] = __df_locs.apply(
            lambda x: x['TotalDrivers'] - x['Employed'], axis=1)

        __df_locs.sort_values(
            by=['TotalDrivers'], ascending=False, inplace=True)

        __df_locs['ScnName'] = UI_SHIFT_DATA.scn_name
        __df_locs['Weekday'] = weekday

        __df_locs = __df_locs[__df_locs.TotalDrivers > 0].copy()
        del __dct_loc_fixed_drivers, __dct_loc_drivers, __set_drivers, __fixed_tours

    except Exception:
        __err = log_exception(
            popup=False, remarks='Generating loc details failed!')
        log_message(message=__err,
                   module_name='kpi_report/__loc_details')

        return DataFrame()

    return __df_locs.loc[:, [
        'Weekday', 'loc_code', 'UnFixed', 'Fixed', 'Employed', 'Subco', 'TotalDrivers', 'ScnName']].copy()