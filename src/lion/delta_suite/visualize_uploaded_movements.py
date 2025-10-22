from datetime import datetime
from lion.config.libraries import PICKLE_DUMPS
from lion.delta_suite.build_tour import build_temp_tour
from lion.delta_suite.delta_logger import DELTA_LOGGER
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.utils.sqldb import SQLDB
from lion.create_flask_app.create_app import LION_FLASK_APP


def build_single_movement_schedule():
    """
    Builds and stores a single movement schedule for drivers based on uploaded movements to allow
    possibility of visualisation of uploaded movements. If DELTA_LOGGER.DF_MOVEMENTS_EXCLUDED_FROM_OPT is not empty,
    it will be used to construct single movement tours as a subset of movements such as Artics, for example, have already been selected
    for optimization. 
    
    This function performs the following steps:
    - Copies movement data from DELTA_LOGGER.DF_MOVEMENTS.
    - Validates that movement data exists.
    - Constructs a DataFrame with driver and shift information, including locations, vehicle types, and schedule flags.
    - Calculates driving time and distance for each movement using UI_RUNTIMES_MILEAGES.
    - Sets weekday flags (Monday to Friday) as active.
    - Adds a timestamp for record creation.
    - Serializes movement tour data using PICKLE_DUMPS and build_temp_tour.
    - Prepares the DataFrame with relevant columns and stores it in the 'local_drivers_info' in the database.
    - Logs exceptions if any errors occur during processing.
    Returns:
        str: 'OK' if the schedule is built successfully.
    """
    
    try:
        # Here we build the local drivers info table
        # This table is used to store the information about the drivers and their shifts which is a single movement

        df_movements_excluded = DELTA_LOGGER.DF_MOVEMENTS_EXCLUDED_FROM_OPT.copy()
        local_drivers_info = DELTA_LOGGER.DF_MOVEMENTS.copy() if df_movements_excluded.empty else df_movements_excluded.copy()

        DELTA_LOGGER.log_info(f"Building visualisation for {local_drivers_info.shape[0]} movements ...")

        if local_drivers_info.empty and df_movements_excluded.empty:
            raise Exception("No movements data has been provided!")
        
        del df_movements_excluded
        
        local_drivers_info['ctrl_loc'] = local_drivers_info['From']
        local_drivers_info['start_loc'] = local_drivers_info['From']
        local_drivers_info['shiftname'] = local_drivers_info.apply(lambda x: f"{x['ctrl_loc']}.{x['shift_id']}", axis=1)
        local_drivers_info['operator'] = 1
        local_drivers_info['home_base'] = local_drivers_info['VehicleType'].apply(
            lambda x: 1 if x == 'Tractor-trailer 2/3 Axles 80m3' else 0)
        local_drivers_info['vehicle'] = local_drivers_info['VehicleType'].apply(
            lambda x: 1 if x == 'Tractor-trailer 2/3 Axles 80m3' else 4)
        local_drivers_info['double_man'] = 0
        local_drivers_info['loc'] = local_drivers_info['From']
        local_drivers_info['sun'] = 0
        local_drivers_info['sat'] = 0

        local_drivers_info['DrivingTime'] = local_drivers_info.apply(lambda x: UI_RUNTIMES_MILEAGES.get_movement_driving_time(orig=x['From'],
                                                                                dest=x['To'], vehicle=int(x['vehicle'])), axis=1)
        
        local_drivers_info['Distance'] = local_drivers_info.apply(lambda x: UI_RUNTIMES_MILEAGES.get_movement_dist(orig=x['From'],
                                                                                dest=x['To'], vehicle=int(x['vehicle'])), axis=1)

        for dy in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
            local_drivers_info[dy.lower()] = 1

        local_drivers_info['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        local_drivers_info['data'] = local_drivers_info.apply(
            lambda x: PICKLE_DUMPS(build_temp_tour(shift_id=x['shift_id'], m=x['movement_id'], deptime=x['DepTime'], depday=x['DepDay'],
                                                    driving_time=x['DrivingTime'], loc_from=x['From'], 
                                                    loc_to=x['To'], dist=x['Distance'])), axis=1)

        local_drivers_info['del_flag'] = 0

        local_drivers_info = local_drivers_info[['shift_id', 'shiftname', 'ctrl_loc', 'start_loc', 'operator', 'home_base',
                                                    'double_man', 'vehicle', 'loc', 'mon', 'tue', 'wed', 'thu', 'fri',
                                                    'sat', 'sun', 'timestamp', 'data', 'del_flag']].copy()



        local_drivers_info['user_id'] = LION_FLASK_APP.config['LION_USER_ID']
        local_drivers_info['group_name'] = LION_FLASK_APP.config['LION_USER_GROUP_NAME']

        SQLDB.to_sql(dataFrame=local_drivers_info,
                                destTableName='local_drivers_info', ifExists='replace')
            

    except Exception as e:
        DELTA_LOGGER.log_exception(message=f"Error building local drivers info. {str(e)}")
