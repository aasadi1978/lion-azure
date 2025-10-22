from lion.delta_suite.visualize_uploaded_movements import build_single_movement_schedule
from lion.delta_suite.delta_logger import DELTA_LOGGER
from lion.delta_suite.read_locations import read_locations
from lion.delta_suite import read_movements
from lion.delta_suite.read_runtimes import read_runtimes
from lion.delta_suite.configure_delta_input_data import check_and_set_delta_data_sources
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.orm.shift_movement_entry import ShiftMovementEntry
from pandas import DataFrame
from lion.utils.dispose_db_engine import shutdown_db_engine
from lion.utils.sqldb import SQLDB
from lion.orm.drivers_info import DriversInfo
from lion.optimization import clear_cache

def read_delta_movements():
    """
    Reads and processes delta movements, updating relevant database tables and handling errors.
    Note that no temporary schedule will be created as this function is used to read the movements from the Delta database
    and execute optimization steps.

    This function performs the following steps:
    1. Caches the current schedule.
    2. Resets the global delta logger.
    3. Clears all driver and shift movement entries.
    4. Sequentially executes the steps: reading locations, reading runtimes, and building movements and changeovers.
    5. If any step logs a global error, the process is halted and an error status is returned.
    6. Updates the 'scn_info' table in the local schedule database with scenario information.
    7. Handles exceptions by logging them and returning an error status.
    8. Ensures the database engine is shut down after processing.
    9. If an error occurred, imports the database.
    
    Returns:
        dict: A status dictionary with 'code' (int) and 'message' (str) indicating the result of the operation.
    """
    DELTA_LOGGER.reset()
    
    OPT_LOGGER.log_statusbar(message='Validating delta data sources ... ')
    if not check_and_set_delta_data_sources():

        return {
            'code': 400,
            'message': f"Delta data validation failed! {DELTA_LOGGER.DELTA_GLOBAL_ERROR}"
        }

    OPT_LOGGER.log_statusbar(message='Reading Delta movements ... ')
    
    status = {
        'code': 200,
        'message': ''
    }

    # clean up the database
    DriversInfo.clear_all()
    ShiftMovementEntry.clear_all()

    try:
        for step in [read_locations, # Read locations and determine, potentially overwrite region
                     read_runtimes,
                     read_movements.build_movements_n_changeovers,
                     build_single_movement_schedule]:

            step()
            if DELTA_LOGGER.DELTA_GLOBAL_ERROR:
                OPT_LOGGER.log_exception(message=f"Error: {DELTA_LOGGER.DELTA_GLOBAL_ERROR}")

                status = {
                    'code': 400,
                    'message': DELTA_LOGGER.DELTA_GLOBAL_ERROR
                }
                return status

        scn_info = DataFrame([['scn_name', 'Delta movements' ]], columns=['param', 'val'])
        SQLDB.to_sql(dataFrame=scn_info, destTableName='scn_info', ifExists='replace')

        clear_cache.clear_all()

    except Exception:
        DELTA_LOGGER.log_exception(message=f"Error during conversion process.")
        status = {
            'code': 400,
            'message': DELTA_LOGGER.DELTA_GLOBAL_ERROR
        }

        OPT_LOGGER.log_exception(message=f"Error: {DELTA_LOGGER.DELTA_GLOBAL_ERROR}")

    finally:
        shutdown_db_engine()

    return status

def import_delta_data():
    """
    This method is the entry point for the conversion process.
    It reads the locations, runtimes, and builds the local schedule database.
    """

    DELTA_LOGGER.reset()
    if not check_and_set_delta_data_sources():

        return {
            'code': 400,
            'message': f"{DELTA_LOGGER.DELTA_GLOBAL_ERROR}"
        }

    status = {
        'code': 200,
        'message': ''
    }

    try:

        for step in [read_locations, 
                     read_runtimes, 
                     read_movements.build_movements_n_changeovers, 
                     build_single_movement_schedule]:
            
            step()
            if DELTA_LOGGER.DELTA_GLOBAL_ERROR:
                status = {
                    'code': 400,
                    'message': DELTA_LOGGER.DELTA_GLOBAL_ERROR
                }
                return status

        scn_info = DataFrame([['scn_name', 'Delta movements' ]], columns=['param', 'val'])
        SQLDB.to_sql(dataFrame=scn_info, 
                     destTableName='scn_info', 
                     ifExists='replace')

    except Exception:
        DELTA_LOGGER.log_exception(message=f"Error during conversion process.")
        status = {
            'code': 400,
            'message': DELTA_LOGGER.DELTA_GLOBAL_ERROR
        }

    finally:
        shutdown_db_engine()

    return status