from lion.optimization.gurobi.gurobi_installation import verify_gurobi_installation
from lion.ui.ui_params import UI_PARAMS
from lion.logger.exception_logger import log_exception

def cache_optimization_params(**kwargs):

    try:

        kwargs.update({'excluded_locs': ';'.join(
            kwargs.get('excluded_locs', []))})

        UI_PARAMS.DRIVING_TIME_B4_BREAK = int(kwargs.get('drivingtimeb4break', 270))
        UI_PARAMS.MIN_BREAK_TIME_WORKING = int(kwargs.get('minbreaktimeworking', 30))
        UI_PARAMS.WORKING_TIME_B4_BREAK = int(kwargs.get('workingtimeb4break', 360))
        UI_PARAMS.MIN_BREAK_TIME = int(kwargs.get('minbreaktime', 60))
        UI_PARAMS.MAX_REPOS_DRIV_MIN = int(kwargs.get('maxreposdrivmin', 270))
        UI_PARAMS.MAXIMUM_DOWNTIME = int(kwargs.get('maxcontime', 360))
        UI_PARAMS.MAX_TOUR_DUR = int(kwargs.get('maxtourdur', 720))
        UI_PARAMS.MAX_DRIVING_DUR = int(kwargs.get('maxdrivingdur', 720))
        UI_PARAMS.DOUBLE_MAN_SHIFT_DUR = int(kwargs.get('dblman_shift_dur', 0))

        grb_OK = (UI_PARAMS.MIP_SOLVER == 'Gurobi' and verify_gurobi_installation())
        
        if not grb_OK:
            UI_PARAMS.MIP_SOLVER = 'OR-Tools/CBC'

    except Exception:
        return {'Message': log_exception(popup=False, remarks='Caching optimization settings failed!')}

    return {'Message': ''}