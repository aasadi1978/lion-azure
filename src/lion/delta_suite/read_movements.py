from datetime import datetime, timedelta, time
from lion.config import paths
from lion.bootstrap.constants import INIT_LOADED_MOV_ID, LION_DATES
from lion.config.libraries import OS_PATH
from lion.delta_suite.delta_logger import DELTA_LOGGER
from lion.optimization.opt_params import OPT_PARAMS
from pandas import DataFrame, concat
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.utils.sqldb import SQLDB
from lion.xl.write_excel import xlwriter
from lion.orm.orm_runtimes_mileages import RuntimesMileages
from lion.orm.location import Location
from lion.create_flask_app.create_app import LION_FLASK_APP


global mov_id
mov_id = INIT_LOADED_MOV_ID


def get_mov_id():
    global mov_id
    mov_id += 1
    return mov_id

def _time2datetime(timeobj):
    try:

        if isinstance(timeobj, time):
            time_str = timeobj.strftime('%H%M')
        elif isinstance(timeobj, str):
            time_str = (timeobj.replace(':', '') if ':' in timeobj else timeobj)[:4]
        else:
            time_str = str(timeobj)[:4]
        
        if time_str in ['', '0000']:
            time_str = '0001'

        time_obj = datetime.strptime(time_str, '%H%M').time()

        dt = datetime.combine(LION_DATES['Mon'], time_obj)
        return dt + timedelta(hours=12)
    
    except ValueError as e:
        DELTA_LOGGER.log_exception(f"Error converting time {timeobj} to datetime: {str(e)}")
        return None
    
    except Exception as e:
        DELTA_LOGGER.log_exception(f"Unexpected error in _time2datetime for {timeobj}: {str(e)}")
        return None


def copy_to_opt_movements(df_local_movements):
    """
    Updates the 'opt_movements' table in the database with optimized movement data from the provided DataFrame.
    Args:
        df_local_movements (pd.DataFrame): DataFrame containing movement data with at least the columns 
            'movement_id', 'str_id', 'loc_string', and 'tu_dest'.
    Process:
        - Selects relevant columns from the input DataFrame.
        - Adds a current timestamp to each row.
        - Sets weekday columns ('mon' to 'fri') to 1, 'sun' to 0.
        - Adds 'shift_id' (set to 0) and 'user' (current user or 'System').
        - Writes the resulting DataFrame to the 'opt_movements' table in the database, replacing existing data.
    Exception Handling:
        - Logs and updates status if any exception occurs during the process.
    Returns:
        bool: False if an exception occurs, otherwise None.
    """
    try:
        df_local_movements_opt = df_local_movements[['movement_id', 'str_id','loc_string', 'tu_dest']].copy()
        df_local_movements_opt['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for dy in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
            df_local_movements_opt[dy.lower()] = 1
        
        df_local_movements_opt['sun'] = 0
        df_local_movements_opt['shift_id'] = 0
        df_local_movements_opt['user'] = LION_FLASK_APP.config['LION_USER_ID']

        SQLDB.to_sql(dataFrame=df_local_movements_opt[
            ['movement_id', 'str_id', 'loc_string', 'tu_dest', 'timestamp', 'mon', 'tue', 'wed', 
                'thu', 'fri', 'sun', 'shift_id', 'user']],
            destTableName='opt_movements', ifExists='replace')
        
    except Exception as e:
        DELTA_LOGGER.log_exception(f"Error copying movements: {str(e)}")
        return False

def validate_movement_locations(df_movements: DataFrame) -> DataFrame:
    """
    Validates the 'From' and 'To' location codes in the given movements DataFrame.
    This function checks whether the origin ('From') and destination ('To') location codes in
    `df_movements` exist in the list of valid location codes. Movements with invalid location
    codes are separated, logged, and saved to a CSV file for review. The function returns a
    DataFrame containing only the valid movements.
    
    Args:
        df_movements (DataFrame): DataFrame containing movement records with 'From' and 'To' columns.
    Returns:
        DataFrame: DataFrame containing only movements with valid 'From' and 'To' location codes.
                   If an exception occurs, returns an empty DataFrame.
    Side Effects:
        - Logs the number of invalid movements and the path to the CSV file containing them.
        - Saves invalid movements to a timestamped CSV file in the DELTA_DATA_PATH directory.
        - Logs exceptions if any errors occur during validation.
    """
    try:

        loc_codes = list(Location.to_dict(clear_cache=True))

        df_invalid_origin = df_movements[~df_movements['From'].isin(loc_codes)].copy()
        df_movements = df_movements[df_movements['From'].isin(loc_codes)].copy()

        df_invalid_destination = df_movements[~df_movements['To'].isin(loc_codes)].copy()
        df_movements = df_movements[df_movements['To'].isin(loc_codes)].copy()

        df_invalid = concat([df_invalid_origin, df_invalid_destination], 
                            ignore_index=True).drop_duplicates().copy()

        if not df_invalid.empty:

            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M')
            df_invalid['timestamp'] = timestamp

            df_invalid.to_csv(paths.DELTA_DATA_LOG_PATH / f'invalid_movements-{timestamp}.csv', 
                              index=False, header=True, encoding='utf-8-sig'
                              )

            DELTA_LOGGER.log_statusbar(
                message=f"Found {df_invalid.shape[0]} invalid movements. " + \
                     f"Check '{paths.DELTA_DATA_LOG_PATH / f'invalid_movements-{timestamp}.csv'}' for details.")

        return df_movements
        
    except Exception as e:
        DELTA_LOGGER.log_exception(f"Error validating movement locations: {str(e)}")
        return DataFrame()


def build_movements_n_changeovers():

    UI_RUNTIMES_MILEAGES.reset()
    

    error_occurred = False

    try:
        # this dataframe has been set and updated in the previous step, i.e., validated and loaded
        if DELTA_LOGGER.DF_MOVEMENTS.empty:
            raise Exception("No movements data available to process.")
        
        df_movements_data = DELTA_LOGGER.DF_MOVEMENTS.copy()
        df_movements_data = df_movements_data[['FromLocation', 'ToLocation', 'VehicleType', 'DepTime']].copy()

        df_movements_data['MovementID'] = [get_mov_id() for _ in range(df_movements_data.shape[0])]
        df_movements_data.rename(columns={'FromLocation': 'From', 'ToLocation': 'To'}, inplace=True)
        df_movements_data['From'] = df_movements_data['From'].str.strip().str.upper()
        df_movements_data['To'] = df_movements_data['To'].str.strip().str.upper()


        df_movements_data = validate_movement_locations(df_movements_data)

        if df_movements_data.empty:
            raise Exception("No valid movements data available to process.")

        df_movements_data = df_movements_data[df_movements_data.VehicleType.fillna('T-Blank').str.lower() != 'colocated'].copy()
        df_movements_data['DepDateTime'] = df_movements_data.DepTime.apply(_time2datetime)

        df_movements_data['VehicleType'] = df_movements_data.VehicleType.apply(lambda x: 'Tractor-trailer 2/3 Axles 80m3' 
                                                                               if x.upper().startswith('T') else 'Van (standard)')
        
        df_movements_data = df_movements_data[df_movements_data['VehicleType'].str.lower() != 'colocated'].copy()
        
        df_movements_data['DepTime'] = df_movements_data['DepDateTime'].apply(lambda x: x.strftime('%H%M'))
        df_movements_data['DepDay'] = df_movements_data.DepDateTime.apply(lambda x: [idx for idx, dy in enumerate(LION_DATES) 
                                                                        if dy == x.strftime('%a')][0])
        df_movements_data['TrafficType'] = 'Express'
        df_movements_data['InScope'] = 'TRUE'
        df_movements_data['tu'] = ''
        df_movements_data['loc_string'] = df_movements_data.apply(lambda x: '.'.join([str(x['From']), str(x['To']), str(x['DepTime'])]), axis=1)   

        df_movements_data['Mon'] = 1
        df_movements_data['Tue'] = 1
        df_movements_data['Wed'] = 1
        df_movements_data['Thu'] = 1
        df_movements_data['Fri'] = 1
        df_movements_data['Sun'] = 0
        df_movements_data['Comments'] = ''

        df_movements_data = df_movements_data[['MovementID', 'loc_string', 'From', 'To', 'tu', 
                                                'DepDay', 'DepTime', 'TrafficType', 'VehicleType', 
                                                'InScope', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sun', 
                                                'Comments']].copy()

        df_local_movements = df_movements_data[['MovementID', 'loc_string', 'From', 'To', 'tu', 'DepDay', 
                                                'DepTime', 'TrafficType', 'VehicleType']].copy()
        
        df_local_movements['vehicle_type'] = df_local_movements['VehicleType'].apply(lambda x: 1 if x == 'Tractor-trailer 2/3 Axles 80m3' else 4)
        df_local_movements.rename(columns={'MovementID': 'movement_id'}, inplace=True)

        df_local_movements['shift_id'] = [x + 1000 for x in range(1, len(df_local_movements) + 1)]

        if OPT_PARAMS.USER_VEHICLE_ID:
            DELTA_LOGGER.log_statusbar(
                message=f"Filtering movements for vehicle type {OPT_PARAMS.USER_VEHICLE_ID} ... ")
            
            df_local_movements['shift_id'] = df_local_movements.apply(
                lambda x: 0 if x['vehicle_type'] == OPT_PARAMS.USER_VEHICLE_ID else x['shift_id'], axis=1)
            
        df_local_movements = validate_runtimes_data(df_local_movements)
        if df_local_movements.empty:
            raise Exception("No valid movements found.")

        df_local_movements['str_id'] = df_local_movements.apply(
            lambda x: f"{x['From']}|{x['To']}|{x['DepDay']}|{x['DepTime']}|{x['vehicle_type']}|{x['TrafficType']}", axis=1)

        df_local_movements['extended_str_id'] = df_local_movements.apply(
            lambda x: f"{x['From']}|{x['To']}|{x['DepDay']}|{x['DepTime']}|{x['vehicle_type']}|{x['TrafficType']}|{x['movement_id']}", axis=1)
        
        df_local_movements['is_loaded'] = 1
        df_local_movements['loc_string'] = ''
        df_local_movements['tu_dest'] = ''

        df_local_movements['group_name'] = LION_FLASK_APP.config['LION_USER_GROUP_NAME']
        df_local_movements['user_id'] = LION_FLASK_APP.config['LION_USER_ID']

        df_local_movements[['shift_id', 'movement_id', 'extended_str_id', 'str_id', 
                            'is_loaded', 'loc_string', 'tu_dest', 'user_id', 'group_name']].copy()
        
        SQLDB.to_sql(dataFrame=df_local_movements,
                                destTableName='local_movements', ifExists='replace')

        DELTA_LOGGER.update_df_movements(df_local_movements[df_local_movements.shift_id == 0].copy())
        DELTA_LOGGER.update_df_movements_excluded(df_local_movements[df_local_movements.shift_id > 0].copy())

        copy_to_opt_movements(DELTA_LOGGER.DF_MOVEMENTS.copy())
        
        SQLDB.empty_table(tablename='local_changeovers')
        
        # Dumps only movements with shift_id == 0
        xlwriter(df=DELTA_LOGGER.DF_MOVEMENTS.copy(), 
                    xlpath=OS_PATH.join(paths.LION_OPTIMIZATION_PATH, 'movements.xlsm'), 
                    sheetname='Movements', 
                    keep=False, 
                    header=True, 
                    echo=False)

    except Exception:
        error_occurred = True
        DELTA_LOGGER.update_df_movements(DataFrame())
        DELTA_LOGGER.log_exception(message=f"Error processing delta movements xlsx file.")

    return not error_occurred

def validate_runtimes_data(df_move_data):

    try:
        if df_move_data.empty:
            raise Exception("No movements data available to validate runtimes.")

        DELTA_LOGGER.log_statusbar(message='Validating runtimes data for the movements ... ')
        _df_move_data = df_move_data.copy()
        list_tuples = zip(
            _df_move_data['From'].str.strip().str.upper(),
            _df_move_data['To'].str.strip().str.upper(),
            _df_move_data['vehicle_type'],
        )

        runtimes_tuples = RuntimesMileages.get_existing_tuples()
        missing_runtimes = [tpl for tpl in list_tuples if tpl not in runtimes_tuples]

        if missing_runtimes:

            DELTA_LOGGER.log_statusbar(
                message=f"There are {len(missing_runtimes)} movements without runtimes. We remove them from the movements data.")

            df_move_data['remove_flag'] = df_move_data.apply(
                lambda x: (x['From'].strip().upper(), x['To'].strip().upper(), x['vehicle_type']) in missing_runtimes, axis=1)
            

            df_move_data_removed = df_move_data[df_move_data['remove_flag']].copy()
            df_move_data = df_move_data[~df_move_data['remove_flag']].copy()

            df_move_data.drop(columns=['remove_flag'], inplace=True)
            df_move_data_removed.drop(columns=['remove_flag'], inplace=True)

            if not df_move_data_removed.empty:
                
                timestamp = datetime.now().strftime('%Y-%m-%d-%H%M')
                df_move_data_removed['timestamp'] = timestamp

                DELTA_LOGGER.log_statusbar(
                    message=f"Found {df_move_data_removed.shape[0]} invalid movements due to missing runtimes data. " + \
                        f"Check '{paths.DELTA_DATA_LOG_PATH / f'invalid_movements-no-runtimes-{timestamp}.csv'}' for details.")

                df_move_data_removed.to_csv(
                    OS_PATH.join(paths.DELTA_DATA_LOG_PATH, f'invalid_movements-no-runtimes-{timestamp}.csv'),
                    index=False, header=True, encoding='utf-8-sig'
                )

        return df_move_data

    except Exception as e:
        DELTA_LOGGER.log_exception(f"Error validating runtimes data: {str(e)}")
        return DataFrame()