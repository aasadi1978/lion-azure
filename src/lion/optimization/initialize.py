from collections import defaultdict
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.opt_params import OPT_PARAMS
from lion.ui.ui_params import UI_PARAMS
from lion.utils.elapsed_time import ELAPSED_TIME
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER
from lion.utils.flask_request_manager import retrieve_form_data

def initialize_optimization(**kwargs):
    """
    Initializes the optimization process by resetting and configuring global parameters and logging settings.
    Keyword Args:
        schedule_employed (bool, optional): Indicates if a schedule is employed. Defaults to False.
        optimization_weekdays (list of str, optional): List of weekdays for optimization. Defaults to ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].
        apply_max_drivers_per_loc (bool, optional): Whether to apply a maximum driver count per location. Defaults to False.
        vehicle_code (int or str, optional): Vehicle identifier code. Defaults to 0.
        Additional keyword arguments are passed to OPT_PARAMS.update().
    Returns:
        bool: True if initialization succeeds, False otherwise.
    Side Effects:
        - Resets and updates global optimization parameters (OPT_PARAMS).
        - Initializes or resets the optimization logger (OPT_LOGGER).
        - Creates a temporary directory for optimization outputs.
        - Logs information and exceptions related to the initialization process.
    Typical kwargs = {'page_num': 1, 'vehicle_code': '1', 'n_top_closest_driver_loc': 10, 'empty_downtime': '0,60', 'maxdowntime_maxreposmin_II': '90,90', 
        'apply_max_drivers_per_loc': True, 'schedule_employed': False, 'user_loaded_movs': True, 'recalc_mileages_runtimes': True, 
        'run_extended_optimization': False, 'excl_dblman': False, 'schedule_dblman_movs': True, 'identify_infeas_shifts': False, 
        'excluded_locs': [], 'mip_solver': 'Gurobi', 'drivers': [], 'dblman_shift_dur': '990', 
        'optimization_weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']}

     """

    try:

        if not kwargs:
            kwargs = retrieve_form_data()

        ELAPSED_TIME.reset()
        OPT_PARAMS.reset()
        OPT_LOGGER.reset()
        STATUS_CONTROLLER.reset()

        OPT_PARAMS.OPTIMIZATION_TEMP_DIR = OPT_LOGGER.TEMP_DIR
        OPT_PARAMS.DCT_LANE_RUNTIMES_INFO = defaultdict(dict)
        
        OPT_PARAMS.PAGE_NUM = kwargs.get('page_num', 1)
        OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC = kwargs.get('n_top_closest_driver_loc', 10)
        OPT_PARAMS.MAXDOWNTIME_MAXREPOSMIN = [int(x) for x in kwargs.get('maxdowntime_maxreposmin_II', '90,120').split(',')]
        OPT_PARAMS.APPLY_MAX_DRIVER_CNT = kwargs.get('apply_max_drivers_per_loc', False)
        OPT_PARAMS.SCHEDULE_EMPLOYED_FLAG = kwargs.get('schedule_employed', False)
        OPT_PARAMS.RUN_EXTENDED_OPTIMIZATION = kwargs.get('run_extended_optimization', False)
        OPT_PARAMS.EXCL_DBLMAN = kwargs.get('excl_dblman', False)
        OPT_PARAMS.SCHEDULE_DBLMAN_MOVS = kwargs.get('schedule_dblman_movs', True)
        OPT_PARAMS.EXCLUDED_LOCS = kwargs.get('excluded_locs', [])
        OPT_PARAMS.MIP_SOLVER = kwargs.get('mip_solver', 'Gurobi')
        OPT_PARAMS.DOUBLE_MAN_SHIFT_DUR = int(kwargs.get('dblman_shift_dur', 990))

        OPT_PARAMS.FILTERING_WKDAYS = UI_PARAMS.FILTERING_WKDAYS
        OPT_PARAMS.OPTIMIZATION_WEEKDAYS=kwargs.get(
            'optimization_weekdays', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])
        
        OPT_PARAMS.DCT_MOVEMENTS_TO_OPTIMIZE = {}
        OPT_PARAMS.SETOF_EXCLUDED_MOVEMENTS_FROM_OPT = set()
        if len(OPT_PARAMS.FILTERING_WKDAYS) == 1:
            OPT_PARAMS.OPTIMIZATION_REP_DAY = OPT_PARAMS.FILTERING_WKDAYS[-1]
        else:
            OPT_PARAMS.OPTIMIZATION_REP_DAY = 'Wed'
        OPT_PARAMS.APPLY_MAX_DRIVER_CNT = kwargs.get('apply_max_drivers_per_loc', False)
        OPT_PARAMS.USER_VEHICLE_ID = int(kwargs.get('vehicle_code', 0))

        OPT_LOGGER.log_info(
                message=f"The selected representative day is: {OPT_PARAMS.OPTIMIZATION_REP_DAY}")
        OPT_LOGGER.log_info(
                message=f"The output is valid for the following days: {';'.join(OPT_PARAMS.OPTIMIZATION_WEEKDAYS)}")
    
    except Exception as e:
        __message = f"Initialization failed: {str(e)}"
        OPT_LOGGER.log_exception(message=__message)

        return False
    
    return True
