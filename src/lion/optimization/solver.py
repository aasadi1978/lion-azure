from lion.optimization.gurobi.grb_output import GrbOutput
from os import path as os_path
from datetime import datetime
from lion.optimization.opt_params import OPT_PARAMS
from lion.ui.ui_params import UI_PARAMS
from lion.optimization.gurobi.grb_optimize import Optimize as GrbOptimize
from lion.optimization.or_tools.ortools_optimize import Optimize as CbcOptimize
from lion.create_flask_app.create_app import LION_FLASK_APP


class SolveMIP():

    def __init__(self):

        solver = UI_PARAMS.MIP_SOLVER
        logFile = os_path.join(
            OPT_PARAMS.OPTIMIZATION_TEMP_DIR, 'optimization.log')

        try:

            message = f"MIP Solver log. When: {str(datetime.now())[:19]}. Solver: {solver} By: {LION_FLASK_APP.config['LION_USER_FULL_NAME']}"

            self.__mip_optimizer = None

            if solver.lower() == 'gurobi':
                self.__mip_optimizer = GrbOptimize(log_file=logFile)
            else:
                 self.__mip_optimizer = CbcOptimize(log_file=logFile)

            with open(logFile, 'a') as log_file_opt:
                log_file_opt.writelines(message)

            self.__grb_output = GrbOutput()
            self.__grb_input_data = None

        except Exception as e:
            with open(logFile, 'a') as log_file_opt:
                log_file_opt.writelines(f"Initializing SolveMIP failed. {str(e)}")

            self.__mip_optimizer.update_log(message='Gurobi execution was failed.\n%s' % (
                            self.__mip_optimizer.print_exception()), module_name='execute_gurobi.py/__execute')

    @property
    def grb_input_data(self):
        return self.__grb_input_data

    @grb_input_data.setter
    def grb_input_data(self, __grb_input_data):
        self.__grb_input_data = __grb_input_data

    @property
    def grb_output(self):
        if self.__grb_input_data is not None:
            self.__execute()

        return self.__grb_output

    def __execute(self):

        try:

            if self.__grb_input_data is None:
                raise ValueError('grb_input_data cannot be None!')

            self.__mip_optimizer.reset()
            self.__mip_optimizer.echo = True

            self.__mip_optimizer.dict_tours = self.__grb_input_data.dict_tours
            self.__mip_optimizer.dct_max_n_drivers_per_loc_in_sample = self.__grb_input_data.dct_max_n_drivers_per_loc_in_sample
            self.__mip_optimizer.read_and_optimize()

            self.__grb_output.optimal_tours = self.__mip_optimizer.optimal_tours
            self.__grb_output.set_optimized_input_movements = self.__mip_optimizer.set_optimized_input_movements
            self.__grb_output.dct_loc_driver_count = self.__mip_optimizer.dct_loc_driver_count

        except Exception:

            self.__mip_optimizer.update_log(message='Gurobi execution was failed.\n%s' % (
                self.__mip_optimizer.print_exception()), module_name='execute_gurobi.py/__execute')
