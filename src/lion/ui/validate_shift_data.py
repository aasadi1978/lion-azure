
from datetime import datetime
import logging
from lion.logger.exception_logger import log_exception
from lion.shift_data.build_schedule import BuildSchedule
from lion.shift_data.shift_data import UI_SHIFT_DATA


def load_shift_data_if_needed() -> dict:
    """
    Attempts to load shift data if it is not already loaded.
    Checks if the optimal drivers data is present. If not, it tries to build the schedule and load baseline shift data.
    Updates the scenario name after loading. If loading fails, an exception is raised and handled.
    Returns:
        dict: A dictionary containing the result code and message indicating success or failure.
    """

    exit_code = 200
    message = 'Shift data loaded successfully.'
    t0 = datetime.now()
    try:
        if not UI_SHIFT_DATA.optimal_drivers:

            logging.info("UI_SHIFT_DATA contains no schedule data. Attempting to build schedule and load baseline shift data ...")
            build_status = BuildSchedule().load_baseline_shift_data()
            if build_status:
                scnname = UI_SHIFT_DATA.scn_name
                logging.info(f"Baseline shift data for <-- {scnname} --> loaded successfully.")
                logging.info(f"Number of shifts: {len(UI_SHIFT_DATA.optimal_drivers)}")
                logging.info(f"Number of movements: {len(UI_SHIFT_DATA.dict_all_movements)}")
                UI_SHIFT_DATA.scn_name = scnname
            else:
                message = 'Failed to load baseline shift data.'
                exit_code = 400

    except Exception as e:
        exit_code = 400
        message = f'Error loading shift data. {str(e)}'
        log_exception(popup=False, remarks=message, level='error')

    finally:
        return {'code': exit_code, 'message': message, 
                'time_taken': str(int((datetime.now() - t0).total_seconds())) + ' seconds'}
