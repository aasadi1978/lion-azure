import logging
from pandas import DataFrame
from lion.bootstrap.constants import WEEKDAYS_NO_SAT
from lion.config.paths import LION_LOGS_PATH
from lion.logger.exception_logger import log_exception
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.orm.drivers_info import DriversInfo
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.orm.vehicle_type import VehicleType
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.utils.dfgroupby import df_groupby
from lion.xl.write_excel import xlwriter


def extract_data():

    __days_n_scope = []

    try:

        __days_n_scope.extend(WEEKDAYS_NO_SAT)
        _all_driver_ids = set(UI_SHIFT_DATA.optimal_drivers)
        _all_driver_ids = [shift for shift in _all_driver_ids if shift > 2]

        if not _all_driver_ids:
            raise ValueError(
                f"No shifts found in UI_SHIFT_DATA.optimal_drivers: Type: {type(_all_driver_ids)}")

        movs = ShiftMovementEntry.query.filter(ShiftMovementEntry.shift_id.in_(_all_driver_ids)).all()
        if not movs:
            raise ValueError(
                f"No movements found for shifts: {len(_all_driver_ids)}.")
        
        dct_movements = UI_MOVEMENTS.dict_all_movements
        if not dct_movements:
            logging.warning("dict_all_movements is empty, reloading from DB ...")
            dct_movements = ShiftMovementEntry.to_dict()

        if not dct_movements:
            raise ValueError("No movements found in dict_all_movements.")

        dct_movement_seq = DriversInfo.get_movement_sequence()

        str_movs = ['|'.join([str(MovObj.movement_id), MovObj.str_id, MovObj.loc_string, MovObj.tu_dest, str(
            MovObj.shift_id)]) for MovObj in movs]

        df_all_movements = DataFrame([movstr.split('|') for movstr in str_movs],
                                        columns=['MovementId', 'From', 'To', 'DepDay', 'DepTime', 'VehicleType', 'TrafficType',
                                                'loc_string', 'tu', 'shift_id'])

        df_all_movements['MovementId'] = df_all_movements['MovementId'].astype(int)
        df_all_movements['DepDateTime'] = df_all_movements['MovementId'].apply(lambda x: dct_movements.get(x, {}).get('DepDateTime', None))
        df_all_movements['ArrDateTime'] = df_all_movements['MovementId'].apply(lambda x: dct_movements.get(x, {}).get('ArrDateTime', None))
        df_all_movements['ShiftName'] = df_all_movements['MovementId'].apply(lambda x: dct_movements.get(x, {}).get('shift', None))
        df_all_movements['Sequence'] = df_all_movements['MovementId'].apply(lambda x: dct_movement_seq.get(x, 1))

        df_all_movements = df_all_movements[df_all_movements['ArrDateTime'].notna()].copy()
        
        df_all_movements['ArrDay'] = df_all_movements['ArrDateTime'].apply(lambda x: 0 if x.strftime('%a') == 'Mon' else 1)
        df_all_movements['ArrTime'] = df_all_movements['ArrDateTime'].apply(lambda x: x.strftime('%H:%M'))

        df_all_movements['loc_string'] = df_all_movements.apply(lambda x: x['loc_string'] if len(x['loc_string']) > 0 
                                                                else '.'.join([x['From'], x['To'], x['DepTime']]), axis=1)

        df_all_movements['VehicleType'] = df_all_movements.VehicleType.apply(
            lambda x: VehicleType.get_vehicle_name(vehicle_code=int(x)))

        df_all_movements['ArrDay'] = df_all_movements['ArrDay'].astype(int)
        df_all_movements['DepDay'] = df_all_movements['DepDay'].astype(int)
        df_all_movements['DepTime'] = df_all_movements['DepDateTime'].apply(lambda x: x.strftime('%H:%M'))

        for wkdy in __days_n_scope:

            df_all_movements[wkdy] = df_all_movements.shift_id.apply(lambda x: DriversInfo.shift_id_runs_on_weekday(
                shift_id=int(x), weekday=wkdy))

        df_all_movements = df_groupby(df=df_all_movements,
                                        groupby_cols=[
                                            'ShiftName', 'Sequence', 'loc_string', 'From', 'To', 'tu', 'DepDay',
                                            'DepTime', 'ArrDay', 'ArrTime', 'TrafficType', 'VehicleType'],
                                        agg_cols_dict={wkday: 'max' for wkday in __days_n_scope})

        cols = ['ShiftName', 'Sequence', 'loc_string', 'From', 'To', 'tu', 'DepDay', 
                'DepTime', 'ArrDay', 'ArrTime', 'TrafficType', 'VehicleType']
        
        cols.extend(__days_n_scope)
        df_all_movements = df_all_movements.loc[:, cols].copy()

        df_all_movements.sort_values(
            by=['loc_string', 'DepDay', 'DepTime'], inplace=True)

        xlpath = LION_LOGS_PATH / 'departure_arrival_all_movements.xlsx'

        df_all_movements.rename(columns={'loc_string': 'LocString', 'From': 'Origin', 'To': 'Destination',
                                        'tu': 'TU Destination', 'DepDay': 'DepDay(Today=0)', 'DepTime': 'DepTime(HHMM)',
                                        'ArrDay': 'ArrDay(Today=0)', 'ArrTime': 'ArrTime(HHMM)'}, inplace=True)

        df_all_movements.sort_values(by=['ShiftName', 'Sequence'], inplace=True, ascending=[True, True])
        xlwriter(df=df_all_movements, sheetname='DeparturesArrivals', xlpath=xlpath, header=True)

        del df_all_movements

    except Exception:
        logging.error("Extracting movements failed!")
        return {'code': 400, 'message': f'Extracting departures/arrivals failed! {log_exception(popup=False)}'}

    return {'code': 200, 'message': f'Departures/arrivals file has been successfully saved to {str(xlpath)}'}