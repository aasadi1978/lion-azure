from collections import defaultdict
from lion.config.paths import LION_LOGS_PATH
from lion.reporting.loc_details_kpi import calculate_location_kpis
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.utils.km2mile import km2mile
from lion.utils.safe_copy import secure_copy
from lion.logger.exception_logger import log_exception
from lion.orm.drivers_info import DriversInfo
from lion.orm.location import Location
from lion.utils.concat import concat
from lion.config.libraries import OS_PATH as os_path
from lion.bootstrap.constants import WEEKDAYS_NO_SAT
from pandas import DataFrame
from copy import deepcopy
from lion.xl.write_excel import write_excel as xlwriter
from lion.orm.vehicle_type import VehicleType


def kpi_report(dump_as_xl=False, weekdays=[]):

    return_output = not dump_as_xl

    if not UI_SHIFT_DATA.optimal_drivers:
        if return_output:
            return DataFrame()
        
        return {'code': 400, 'message': 'No schedule has been found!'}

    if not weekdays:
        weekdays.extend(WEEKDAYS_NO_SAT)

    dct_drivers = DriversInfo.to_dict()
    dct_vehicle_names = VehicleType.dict_vehicle_short_name()

    df_locations_kpis = calculate_location_kpis(weekday=weekdays[0])

    if not df_locations_kpis.empty:
        df_locations_kpis.sort_values(
            by=['TotalDrivers'], inplace=True)

    try:

        UI_SHIFT_DATA.calculate_cost()
        __dct_optimal_drivers_base = UI_SHIFT_DATA.optimal_drivers
        __dict_all_movements_base = UI_SHIFT_DATA.dict_all_movements

        __dct_optimal_drivers_base.pop(1, None)
        __dct_optimal_drivers_base.pop(2, None)

    except Exception:
        log_exception(
            popup=False, remarks='Setting base data failed for reporting!')

    dct_footprint = Location.to_dict()

    __n_unplanned_movs = UI_SHIFT_DATA.extract_dct_unplanned_movements(
        count_only=True)

    df_kpis_all = DataFrame()

    for wkday in weekdays:

        try:

            __optimal_drivers = {}

            __dct_optimal_drivers_wkday = secure_copy({d: v for d, v in __dct_optimal_drivers_base.items()
                                                   if DriversInfo.shift_id_runs_on_weekday(shift_id=d, weekday=wkday)})

            shiftids = set(set(__dct_optimal_drivers_wkday))
            while shiftids:

                shift_id = shiftids.pop()
                dct_tour = __dct_optimal_drivers_wkday.pop(shift_id)
                dct_tour.refresh(target_weekday=wkday)

                __optimal_drivers[shift_id] = dct_tour

                del dct_tour

            __dict_all_movements = {}
            __dict_all_movements_base = secure_copy(
                __dict_all_movements_base)

            for m in set(__dict_all_movements_base):

                dct_m = __dict_all_movements_base[m]
                dct_m.modify_dep_day(wkday=wkday)

                __dict_all_movements[m] = dct_m

            __dct_kpis = defaultdict(dict)

            __drivers = set(__optimal_drivers)
            __cTypes = ['Subco', 'Employed']

            __kpinames = ['Drivers Used',
                          'Employed%', 'Subco%',
                          'Empty/Solo Movements',
                          'EmptyMileage', 'EmptyMileage%', 'UnplannedMovements',
                          'Empty/Solo Driving Time (hh:mm)',
                          'Movements', 'Mileage', 'Driving Time (hh:mm)', 'Gap Time (hh:mm)',
                          'AvgLoadedMiles/Tour', 'AvgEmptyMiles/Tour', 'AvgLoadedMovements/Tour',
                          'Shift Time (hh:mm)', 'Cost (GBP)']

            df_kpi = DataFrame()
            df_kpi['KPIName'] = __kpinames  # , 'Total Assigned Linehaul Legs'

            __set_drivers = set(__optimal_drivers)
            __dct_optimal_drivers_contract = defaultdict(list)
            __dct_optimal_drivers_vehicle = defaultdict(list)

            for d in __set_drivers:
                __dct_optimal_drivers_vehicle[dct_drivers.get(
                    d, {}).get('vehicle', 0)].append(d)

                __dct_optimal_drivers_contract['Employed'].append(d) if dct_drivers.get(d, {}).get(
                    'operator', '') == 'FedEx Express' else __dct_optimal_drivers_contract['Subco'].append(d)

            __vehicles = list(__dct_optimal_drivers_vehicle)

            __df = deepcopy(df_kpi)
            __df00 = deepcopy(df_kpi)
            __lst = []

            for vhcle in __vehicles:

                __df0 = __df.copy()
                __df0['Vehicle'] = [vhcle] * len(__kpinames)
                __lst.append(__df0)

            df_kpi = concat(__lst)

            __df = deepcopy(df_kpi)
            __n = __df.shape[0]
            __lst = []

            for ctype in __cTypes:

                __df0 = __df.copy()
                __df0['ContractType'] = [ctype] * __n
                __lst.append(__df0)

            df_kpi = concat(__lst)

            __df00['Vehicle'] = 'All'
            __df00['ContractType'] = 'All'

            df_kpi = concat([df_kpi, __df00])
            del __df00

            while __vehicles:

                __vhcle = __vehicles.pop()
                __cTypes = ['Subco', 'Employed']

                while __cTypes:

                    try:
                        __type = __cTypes.pop()

                        __drivers = list(set(__dct_optimal_drivers_contract[__type]) & set(
                            __dct_optimal_drivers_vehicle[__vhcle]))

                        __tmp_optimal_drivers = {
                            d: __optimal_drivers[d] for d in __drivers}

                        __set_planned_movs = set()

                        for d in set(__tmp_optimal_drivers):
                            __set_planned_movs.update(
                                __tmp_optimal_drivers[d]['list_movements'])

                        __set_planned_movs = [
                            m for m in __set_planned_movs if m in __dict_all_movements]

                        __dict_all_planned_movements = {
                            m: __dict_all_movements[m] for m in __set_planned_movs}

                        __empty_solo = [m for m in __set_planned_movs if 'solo'
                                        in __dict_all_planned_movements[m]['TrafficType'].lower() or
                                        __dict_all_planned_movements[m]['TrafficType'].lower() == 'empty']

                        __dct_kpis[(__vhcle, __type)].update({
                            'Drivers Used': len(__tmp_optimal_drivers),
                            'Empty/Solo Movements': len(__empty_solo),
                            'EmptyMileage': km2mile(int(sum([__dict_all_planned_movements[m]['Dist'] for m in __empty_solo]))),
                            'Empty/Solo Driving Time (hh:mm)': sum([__dict_all_planned_movements[m]['DrivingTime'] + dct_footprint[
                                __dict_all_planned_movements[m]['To']]['chgover_driving_min'] for m in __empty_solo]),
                            'Movements': len(__set_planned_movs),
                            'Mileage': km2mile(int(sum([__dict_all_planned_movements[m]['Dist'] for m in __set_planned_movs]))),
                            'Driving Time (hh:mm)': sum([__dict_all_planned_movements[m]['DrivingTime'] + dct_footprint[
                                __dict_all_planned_movements[m]['To']]['chgover_driving_min'] for m in __set_planned_movs]),
                            # 'Total Work Time (hh:mm)': '',
                            'Gap Time (hh:mm)': sum([__tmp_optimal_drivers[d]['idle_time'] for d in set(__tmp_optimal_drivers)]),
                            'Shift Time (hh:mm)': sum([__tmp_optimal_drivers[d]['total_dur'] for d in set(__tmp_optimal_drivers)]),
                            'Cost (GBP)': sum([__tmp_optimal_drivers[d]['tour_cost'] for d in set(__tmp_optimal_drivers)])
                        })

                    except Exception:
                        log_exception(popup=False)

            __set_planned_movs = set()
            for d in set(__optimal_drivers):
                __set_planned_movs.update(
                    __optimal_drivers[d]['list_movements'])

            __set_planned_movs = [
                m for m in __set_planned_movs if m in __dict_all_movements]

            __n_all_drivers = len(__optimal_drivers)
            __employed_pct = len(
                __dct_optimal_drivers_contract['Employed']) / __n_all_drivers
            __subco_pct = len(
                __dct_optimal_drivers_contract['Subco']) / __n_all_drivers

            __empty_solo = [m for m in __set_planned_movs if 'solo' in __dict_all_movements[m]['TrafficType'].lower() or
                            __dict_all_movements[m]['TrafficType'].lower() == 'empty']

            __loaded_m = [
                m for m in __set_planned_movs if m not in __empty_solo]
            __empty_miles = int(
                sum([__dict_all_movements[m]['Dist'] for m in __empty_solo]))

            __total_miles_loaded = int(
                sum([__dict_all_movements[m]['Dist'] for m in __loaded_m]))

            __total_miles = int(
                sum([__dict_all_movements[m]['Dist'] for m in __set_planned_movs]))

            __dct_kpis[('All', 'All')].update({
                'Employed%': int(__employed_pct * 100 + 0.5),
                'Subco%': int(__subco_pct * 100 + 0.5),
                'AvgLoadedMiles/Tour': km2mile(__total_miles_loaded)/__n_all_drivers,
                'AvgEmptyMiles/Tour': km2mile(__empty_miles)/__n_all_drivers,
                'AvgLoadedMovements/Tour': len(__loaded_m)/__n_all_drivers,
                'EmptyMileage%': int(0.5 + __empty_miles * 100/__total_miles),
                'Drivers Used': __n_all_drivers,
                'UnplannedMovements': __n_unplanned_movs,
                'Empty/Solo Movements': len(__empty_solo),
                'EmptyMileage': km2mile(__empty_miles),
                'Empty/Solo Driving Time (hh:mm)': sum([__dict_all_movements[m]['DrivingTime'] + dct_footprint[
                    __dict_all_movements[m]['To']]['chgover_driving_min'] for m in __empty_solo]),
                'Movements': len(__set_planned_movs),
                'Mileage': km2mile(__total_miles),
                'Driving Time (hh:mm)': sum([__dict_all_movements[m]['DrivingTime'] + dct_footprint[
                    __dict_all_movements[m]['To']]['chgover_driving_min'] for m in __set_planned_movs]),
                # 'Total Work Time (hh:mm)': '',
                'Gap Time (hh:mm)': sum([__optimal_drivers[d]['idle_time'] for d in set(__optimal_drivers)]),
                'Shift Time (hh:mm)': sum([__optimal_drivers[d]['total_dur'] for d in set(__optimal_drivers)]),
                'Cost (GBP)': sum([__optimal_drivers[d]['tour_cost'] for d in set(__optimal_drivers)])
            })

            __dct_kpis = dict(__dct_kpis)
            del __tmp_optimal_drivers, __optimal_drivers, __dict_all_movements

            df_kpi['Value'] = df_kpi.apply(
                lambda x: __dct_kpis[(x['Vehicle'], x['ContractType'])].get(x['KPIName'], 0), axis=1)

            df_kpi['ScnName'] = UI_SHIFT_DATA.scn_name
            df_kpi['Weekday'] = wkday

            df_kpi['Vehicle'] = df_kpi.Vehicle.apply(
                lambda x: dct_vehicle_names.get(x, x) if x != 'All' else x)

            if return_output:

                df_kpi['Vehicle_CType_KPI_Weekday'] = df_kpi.apply(lambda x: '-'.join(
                    [x[c] for c in ['Vehicle', 'ContractType', 'KPIName', 'Weekday']]), axis=1)

                df_kpi = df_kpi.loc[:, ['Vehicle_CType_KPI_Weekday', 'Weekday', 'Vehicle', 'ContractType',
                                        'KPIName', 'Value', 'ScnName']].copy()

                df_kpi['INDX'] = df_kpi.Vehicle_CType_KPI_Weekday.tolist()

                __df = df_kpi.copy()
                __df.set_index(['INDX'], inplace=True)
                dct_kpi = __df.Value.to_dict()

                df_locations_kpis['INDX'] = df_locations_kpis.loc_code.tolist()
                __df2 = df_locations_kpis.copy()
                __df2.set_index(['INDX'], inplace=True)
                dct_loc = __df2.TotalDrivers.to_dict()

                df_kpi.sort_values(
                    by=['Weekday', 'Vehicle'], ascending=True, inplace=True)

                return {UI_SHIFT_DATA.scn_name: {'status': 'OK', 'df_kpi': df_kpi, 'df_loc': df_locations_kpis, 'dct_kpi': dct_kpi, 'dct_loc': dct_loc}}

            df_kpis_all = concat([df_kpis_all, df_kpi])

            del __dct_kpis

        except Exception:

            log_exception(
                popup=False, remarks=f'Generating KPI report failed for {wkday}!')

            df_kpi = DataFrame()
            dct_kpi = {}
            dct_loc = {}

            if return_output:
                return {UI_SHIFT_DATA.scn_name: {'status': 'NOK', 'df_kpi': df_kpi, 'df_loc': df_locations_kpis, 'dct_kpi': dct_kpi, 'dct_loc': dct_loc}}

    df_kpis_all = df_kpis_all.loc[:, ['Weekday', 'Vehicle', 'ContractType',
                                      'KPIName', 'Value', 'ScnName']].copy()

    try:
        df_kpis_all.sort_values(
            by=['Weekday', 'Vehicle', 'ContractType'], inplace=True)

        xlwriter(df=df_kpis_all, sheetname='kpis',  xlpath=os_path.join(
            LION_LOGS_PATH, 'kpi-report.xlsx'), echo=False)

        xlwriter(df=df_locations_kpis, sheetname='LocDrivers',  xlpath=os_path.join(
            LION_LOGS_PATH, 'kpi-report.xlsx'), keep=True, echo=False)
    
    except Exception:
        return {'code': 400, 'message': log_exception(
            popup=False, remarks='Generating KPI report failed!')}

    return {'code': 200, 'message': f'KPI report generated successfully in {str(LION_LOGS_PATH)}!'}

