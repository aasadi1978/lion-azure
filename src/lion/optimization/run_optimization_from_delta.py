from lion.delta_suite.delta_logger import DELTA_LOGGER
from lion.delta_suite.import_delta_into_lion_main import read_delta_movements
from lion.optimization.orm.opt_movements import OptMovements
from lion.optimization.driver_optimization import DRIVER_OPTIMIZATION
from lion.optimization.extract_locations_info import extract_locs_data
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.optimization.preprocessing import pre_processing
from lion.optimization.read_user_movements.build_baseline_movements import build_baseline_dct_movements
from lion.utils.flask_request_manager import retrieve_form_data
from lion.optimization.initialize import initialize_optimization
from lion.optimization.report_kpi import dump_kpi_reports
from lion.optimization.post_processing import post_processing
from lion.optimization.optimization_logger import OPT_LOGGER

def import_delta_info_and_build():
    """
    Reads and processes delta movements, initializes optimization, and runs a sequence of scheduling steps.
    Returns:
        dict: A status dictionary with 'code' and either 'message' or 'error' keys, indicating the result of the operation.
    Workflow:
        1. Initializes optimization using form data.
        2. Reads delta movements and checks for errors.
        3. Validates the presence of movement records.
        4. Executes a series of optimization steps:
            - Extracts location and driver resource data.
            - Calculates recommended driver locations per lane.
            - Builds baseline movement dictionaries.
            - Runs pre-processing, driver optimization, post-processing, and KPI report dumping.
        5. Handles and logs exceptions during each step.
        6. Returns appropriate status and error messages based on the process outcome.
    """

    if initialize_optimization(**retrieve_form_data()):

        dct_status = read_delta_movements()
        if dct_status.get('code', 200) != 200:
            UI_SHIFT_DATA.reset()
            return dct_status

        if DELTA_LOGGER.DELTA_GLOBAL_ERROR:
            return {'code': 400, "message": DELTA_LOGGER.DELTA_GLOBAL_ERROR}

        records = OptMovements.query.all()

        if not records:
            return {'code': 400,
                    "error": 'No movements is available for optimization! Upload movements xlsx file.'}

        
        run_schedule_optimization_steps = [
            pre_processing,
            DRIVER_OPTIMIZATION.initialize_and_run,
            post_processing,
            dump_kpi_reports
            ]
        
        running_optimization_steps = [
            extract_locs_data, # Extract locations and driver resources and refreshes 'loc_params' in lion.db
            build_baseline_dct_movements, # Builds dct_all_movements and dct_movements_to_optimize
            *run_schedule_optimization_steps # Optimizes the schedule based on the movements and driver locations
        ]
        
        for optimization_step in running_optimization_steps:

            try:
                optimization_step()
            except Exception:
                OPT_LOGGER.log_exception('Error while running optimization_step!')

            if OPT_LOGGER.OPT_GLOBAL_ERROR:
                return {'code': 400, "message": OPT_LOGGER.OPT_GLOBAL_ERROR}
        

        return {'code': 200, "message": "Schedule construction completed."}

    return {'code': 400, "message": f"Failed to initialize optimization. {OPT_LOGGER.OPT_GLOBAL_ERROR}"}