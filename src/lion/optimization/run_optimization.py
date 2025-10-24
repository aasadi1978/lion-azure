from lion.orm.opt_movements import OptMovements
from lion.optimization import create_kpis
from lion.optimization.driver_optimization import DRIVER_OPTIMIZATION
from lion.optimization.extract_locations_info import extract_locs_data
from lion.optimization.preprocessing import pre_processing
from lion.optimization.read_user_movements.build_baseline_movements import build_baseline_dct_movements
from lion.optimization.read_user_movements.update_local_movements import transfer_new_movements_to_local_database
from lion.optimization.clean_up_shifts_and_movs import clean_up_redundant_shifts_and_movements
from lion.optimization.driver_locs_per_lane import calculate_dct_driver_locs_per_lane
from lion.optimization.excluded_shifts import update_excluded_shifts_and_movements
from lion.optimization.initialize import initialize_optimization
from lion.optimization.report_kpi import dump_kpi_reports
from lion.optimization.post_processing import post_processing
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.validate_optimization_db import validate_optimization_database


def run(*args, **kwargs):

    if validate_optimization_database() and initialize_optimization(*args, **kwargs):

        try:

            full_optimization_steps =  []
            if OptMovements.is_empty():
                return {'code': 400,
                        "error": 'No movements is available for optimization! Upload movements xlsx file.'}

            preproccesing_steps = [
                create_kpis.create,
                extract_locs_data, # Extract locations and driver resources and refreshes 'loc_params' in lion.db
                calculate_dct_driver_locs_per_lane, # creates a dictionary of recommended driver locations per lane
                update_excluded_shifts_and_movements, # Splits shifts and movements based on use filters into in/out of scope
                clean_up_redundant_shifts_and_movements, # Cleans up shifts and movements that are no longer needed
                transfer_new_movements_to_local_database, # Transfers new movements from OptMovements to the local database LocalMovements
                build_baseline_dct_movements, # Builds dct_all_movements and dct_movements_to_optimize
            ]

            run_schedule_optimization_steps = [
                pre_processing,
                DRIVER_OPTIMIZATION.initialize_and_run,
                post_processing,
                dump_kpi_reports
            ]
            
            full_optimization_steps.extend(preproccesing_steps)
            full_optimization_steps.extend(run_schedule_optimization_steps)

        except Exception:
            pass

        for optimization_step in full_optimization_steps:
            optimization_step()

            if OPT_LOGGER.OPT_GLOBAL_ERROR:
                return {'code': 400, "error": OPT_LOGGER.OPT_GLOBAL_ERROR}

        return {'code': 200, "message": "Optimization completed."}
    
    return {'code': 400, "message": f"Failed to initialize optimization! {OPT_LOGGER.OPT_GLOBAL_ERROR}"}