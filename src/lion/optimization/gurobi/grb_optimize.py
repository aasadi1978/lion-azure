from collections import defaultdict
from datetime import datetime
from os import getenv, listdir, path
from lion.optimization.opt_params import OPT_PARAMS
from lion.orm.drivers_info import DriversInfo
from lion.config.paths import LION_OPTIMIZATION_PATH
from lion.tour.dct_tour import DctTour
from lion.utils.elapsed_time import ElapsedTime
from gurobipy import GRB, Model as grb_Model, quicksum as grb_quicksum
from os.path import join
from lion.orm.location import Location
from lion.orm.user_params import UserParams
from pandas import DataFrame
from linecache import checkcache, getline
from sys import exc_info
from shutil import rmtree
from lion.utils.load_obj import load_obj
from lion.utils.dict2class import Dict2Class
from lion.utils.dfgroupby import groupby as df_groupby
from lion.utils.print2console import display_in_console
from lion.utils.sqldb import SqlDb
from lion.xl.write_excel import write_excel as xlwriter
from lion.logger.log_entry import LogEntry


class Optimize():

    # Examples: https://github.com/Pyomo/PyomoGallery/wiki
    # https://jckantor.github.io/CBE30338/06.04-Linear-Production-Model-in-Pyomo.html
    # Pyomo docs: https://pyomo.readthedocs.io/en/stable/
    # Pyomo website: http://www.pyomo.org/
    # Multiobjective: https://stackoverflow.com/questions/50742999/multi-objective-optimization-example-pyomo

    # Usefull gurobi links:
    # https://www.gurobi.com/documentation/current/quickstart_mac/reading_and_optimizing_a_m.html

    def __init__(self, log_file=None):

        self.__optimization_output_dir = OPT_PARAMS.OPTIMIZATION_TEMP_DIR
        self.__dict_shift_variable_cost = {}

        self.__optimization_log_file = log_file

        self.__list_locations_excluded_from_opt = UserParams.get_param(
            'excluded_locs', if_null='').split(';')

        self.__grb_log_file = join(
            self.__optimization_output_dir, 'gurobi.log')

        with open(self.__grb_log_file, 'w'):
            pass

        __dct_footprint = Location.to_dict()
        self.__set_locs_to_allow_extra_drivers = set([x for x in __dct_footprint.keys() if __dct_footprint[x][
            'loc_type'].lower() in ['station', 'depot', 'hub']])

        del __dct_footprint
        self.reset()

        self.__dct_grb_setting = UserParams.optimization_params()

        self.__TimeLimit = self.__dct_grb_setting.get('TimeLimit', 900)
        self.__MIPGap = float(
            self.__dct_grb_setting.get('MIPGap', 1e-5))

    @property
    def status(self):
        if self.__status == 0:
            self.__optimal_tours = {}

        return self.__status

    @property
    def selected_drivers_tour_pairs(self):
        return self.__selected_drivers_tour_pairs

    @property
    def optimal_tours(self):
        return self.__optimal_tours

    @property
    def dict_tours(self):
        return self.__dict_tours

    @dict_tours.setter
    def dict_tours(self, dct_tours):
        self.__dict_tours = dct_tours

    @property
    def echo(self):
        return self.__echo

    @echo.setter
    def echo(self, echo):
        self.__echo = echo

    @property
    def set_tours_with_infeas_driver(self):
        return self.__set_tours_with_infeas_driver

    @property
    def set_optimal_drivers(self):
        return self.__set_optimal_drivers

    @property
    def set_infeasible_tours(self):
        return self.__set_infeasible_tours

    @property
    def grb_input_data_fname(self):
        return self.__grb_input_data_fname

    @property
    def set_optimized_input_movements(self):
        return self.__set_optimized_input_movements

    @property
    def set_infeas_tours(self):
        return self.__set_infeas_tours

    @property
    def total_cost(self):
        return self.__total_cost

    @property
    def total_number_of_repos(self):
        return self.__total_number_of_repos

    @property
    def dct_loc_driver_count(self):
        __dct = dict(self.__dct_loc_driver_count)
        return {k: v for k, v in __dct.items() if v > 0}

    @property
    def dct_max_n_drivers_per_loc_in_sample(self):
        return self.__dct_max_n_drivers_per_loc_in_sample

    @dct_max_n_drivers_per_loc_in_sample.setter
    def dct_max_n_drivers_per_loc_in_sample(self, x):
        self.__dct_max_n_drivers_per_loc_in_sample = x

    def reset(self):

        self.__dict_shift_variable_cost = {}
        self.__relax_movement_constraint = False
        self.__relax_loc_employed_driver_cnt_cons = False
        self.__set_optimized_input_movements = set()
        self.__dict_tours = {}
        self.__status = 1
        self.__shift_ctrl_location = {}
        self.__set_tours = set()
        self.__dict_driver_tour_pair_variable_cost = {}
        self.__optimal_tours = {}
        self.__set_driver_locs = set()
        self.__set_optimal_drivers = set()
        self.__set_tours_with_infeas_driver = set()
        self.__set_infeasible_tours = set()
        self.__total_cost = 0
        self.__total_number_of_repos = 0
        self.__dct_movement_tours = defaultdict(list)
        self.__dct_dloc_tours = defaultdict(list)
        self.__set_loaded_movements = set()
        self.__dct_loc_driver_count = defaultdict()
        self.__relax_loc_driver_cnt_cons = False
        self.__consider_locs_with_not_allowed_drivers = False
        self.__dct_max_drivers_per_loc = {}
        self.__set_all_driver_locs = set()
        self.__dct_external_grb_data = {}
        self.__selected_drivers_tour_pairs = {}
        self.__dct_max_n_drivers_per_loc_in_sample = {}
        self.__dct_employed_drivers_per_loc = {}

        # This dict contains number of drivers per location throghout the entire network
        # Note that this is different from dct_max_n_drivers_per_loc_in_sample which covers
        # the same data but in a subset of tours being optimized
        # self.__set_all_locations_with_driver_in_whole_nw = set(self.__load_obj(
        #     str_FileName='dct_n_drivers_per_driver_location.json'))

        if not self.__optimization_log_file:

            self.__optimization_log_file = join(
                self.__optimization_output_dir, 'optimization.log')

            with open(self.__optimization_log_file, 'w', errors="ignore", encoding="utf8") as f1:
                f1.writelines(
                    'gurobi optimization has been initialized! Please note that this file is different from gurobi.log.')

    def __read_location_params(self):

        df_loc_params_full = DataFrame()
        try:

            self.__dct_max_drivers_per_loc = {}
            self.__dct_employed_drivers_per_loc = {}

            if OPT_PARAMS.APPLY_MAX_DRIVER_CNT:

                df_loc_params = SqlDb().sqlalchemy_select(
                    tablename='loc_params')

                df_loc_params = df_loc_params[
                    df_loc_params.active == 1].copy()

                df_loc_params['max_allowed_resources'] = df_loc_params.apply(
                    lambda x: max(0, x['un_fixed_employed'] + x['un_fixed_subco'] +
                                    x['extra_employed'] + x['extra_subco']), axis=1)

                df_loc_params['EmployedDrivers'] = df_loc_params.apply(
                    lambda x: max(0, int(x['un_fixed_employed'] + x['extra_employed'])), axis=1)

                __Cols_value = ['EmployedDrivers', 'max_allowed_resources']
                __Cols_value1 = ['EmployedDrivers', 'un_fixed_employed','un_fixed_subco', 'extra_employed', 
                                 'extra_subco', 'max_allowed_resources']

                if not OPT_PARAMS.APPLY_MAX_DRIVER_CNT:
                    __Cols_value1 = ['EmployedDrivers', 'un_fixed_employed','un_fixed_subco', 'extra_employed']

                df_loc_params_full = df_groupby(df_loc_params, groupby_cols=['loc_code'],
                                            agg_cols_dict={c: 'max' for c in __Cols_value1}).copy()

                df_loc_params = df_groupby(df_loc_params, groupby_cols=['loc_code'],
                                            agg_cols_dict={c: 'max' for c in __Cols_value}).copy()
                
                df_loc_params['max_allowed_resources'] = df_loc_params.apply(
                    lambda x: x['EmployedDrivers'] if x['EmployedDrivers'] > x[
                        'max_allowed_resources'] else x['max_allowed_resources'], axis=1)

                df_loc_params = df_loc_params[
                    df_loc_params.max_allowed_resources > 0].copy()
            
                del __Cols_value, __Cols_value1

                df_loc_params.set_index(['loc_code'], inplace=True)
                __dct_loc_params = df_loc_params.to_dict(orient='index')

                self.__dct_employed_drivers_per_loc = {
                    d: __dct_loc_params.get(d, {}).get('EmployedDrivers', 0) for d in self.__set_driver_locs}

                self.__dct_employed_drivers_per_loc = {
                    k: v for k, v in self.__dct_employed_drivers_per_loc.items() if v > 0}

                __list_employed_drivers_with_no_tour = [d for d in set(self.__dct_employed_drivers_per_loc)
                                                        if d not in self.__set_driver_locs]

                if __list_employed_drivers_with_no_tour:

                    for dloc in __list_employed_drivers_with_no_tour:
                        self.__dct_employed_drivers_per_loc.pop(dloc, {})

                    raise ValueError(
                        f"There are driver locations with no tour as options: ';'.join(__list_employed_drivers_with_no_tour)")

                if OPT_PARAMS.APPLY_MAX_DRIVER_CNT:

                    self.__dct_max_drivers_per_loc = {
                        d: __dct_loc_params.get(d, {}).get('max_allowed_resources', 0) for d in self.__set_driver_locs}

                    self.__dct_max_drivers_per_loc = {
                        k: v for k, v in self.__dct_max_drivers_per_loc.items() if v > 0}


                del __dct_loc_params, __list_employed_drivers_with_no_tour


        except Exception:
            self.update_log(message=self.print_exception(popup=False) + ';',
                            module_name='grb_optimize.py/__read_location_params')

        if self.__dct_max_drivers_per_loc:
            self.update_log(message=f"Running gurobi optimization with {len(self.__dct_max_drivers_per_loc)} apply_max_drivers_per_loc",
                            module_name='grb_optimize.py/__read_location_params')

        if self.__dct_employed_drivers_per_loc:
            self.update_log(message=f"Running gurobi optimization with {len(self.__dct_employed_drivers_per_loc)} dct_employed_drivers_per_loc",
                            module_name='grb_optimize.py/__read_location_params')
        
        if df_loc_params_full.empty:
            df_loc_params_full = DataFrame(['No data to show!'], columns=['status'])
                
        df_loc_params_full['ATTENTION'] = 'DO NOT USE THIS FILE AS INPUT'
        try:
            xlwriter(df=df_loc_params_full.copy(),
                sheetname='OptLocParams',  xlpath=join(self.__optimization_output_dir, 'Location_params.xlsx'), 
                echo=False, keep=True)
        except Exception:
            try:
                xlwriter(df=df_loc_params_full.copy(),
                    sheetname='OptLocParams',  xlpath=join(self.__optimization_output_dir, 
                                                           f'OptLocParams-{datetime.now().strftime('%Y-%m-%d %H%M')}.xlsx'), 
                    echo=False, keep=False)

            except Exception:
                self.update_log(message=f"Dumping opt loc params failed!: {self.print_exception(popup=False)}",
                                module_name='grb_optimize.py/__read_location_params')

    def __process_dict_drivers(self, shiftname='ADX.0000'):

        try:

            movs = self.__dict_tours[shiftname]['list_loaded_movements']

            self.__set_loaded_movements.update(movs)
            dloc = shiftname.split('.')[0]

            self.__dct_dloc_tours[dloc].append(shiftname)
            self.__shift_ctrl_location[shiftname] = dloc
            
            self.__dict_driver_tour_pair_variable_cost.update(
                {(dloc, shiftname): self.__dict_tours[shiftname]['tour_variable_cost']})
            
            self.__dict_shift_variable_cost.update(
                {shiftname: self.__dict_driver_tour_pair_variable_cost[(dloc, shiftname)]})

            [self.__dct_movement_tours[m].append(shiftname) for m in movs]

        except Exception:
            self.update_log(message=self.print_exception() + ';',
                            module_name='grb_optimize.py/__process_dict_drivers')

    def dump_constructed_shifts(self):
        try:

            tour_columns = ['shift_id', 'driver', 'dep_date_time', 'arr_date_time', 'shift_end_datetime', 'tour_cntry_from', 'is_complete', 
                'tour_loc_from', 'tour_loc_string', 'total_dur', 'tour_repos_dist', 'tour_input_dist', 'driving_time', 
                'input_driving_time', 'repos_driving_time', 'idle_time', 'break_time', 'is_feas', 'double_man', 'driver_loc_mov_type_key', 
                'tour_variable_cost', 'break_time_cost', 'total_empty_cost', 'idle_time_cost']

            dct_tours_to_dump = {sname: {k: v for k, v in dct_tour.items() if k in tour_columns} 
                                 for sname, dct_tour in self.__dict_tours.items()}
            
            df_tours_to_dump = DataFrame.from_dict(dct_tours_to_dump, orient='index')

            df_tours_to_dump.to_csv(join(self.__optimization_output_dir, 'df_constructed_tours.csv'))
            del df_tours_to_dump
        
        except Exception:
            self.update_log(message=self.print_exception() + ';',
                            module_name='grb_optimize.py/dump_constructed_shifts')
            
    def read_and_optimize(self):

        self.update_log(message='Preprocessing optimization data ...',
                        module_name='grb_optimize.py/read_and_optimize')

        try:

            if not self.__dct_external_grb_data:

                self.__set_tours = set(self.__dict_tours)
                self.__set_all_driver_locs = set([tour_name.split('.')[0] 
                                                  for tour_name in self.__set_tours])

                [self.__process_dict_drivers(shiftname) for shiftname in self.__set_tours]
                
                self.dump_constructed_shifts()

                if getenv('GUROBI_HOME') is None:

                    __dct_process_dict_drivers = {}
                    __dct_process_dict_drivers['set_all_driver_locs'] = self.__set_all_driver_locs
                    __dct_process_dict_drivers['dict_driver_tour_pair_cost'] = self.__dict_driver_tour_pair_variable_cost
                    __dct_process_dict_drivers['set_loaded_movements'] = self.__set_loaded_movements
                    __dct_process_dict_drivers['dct_max_n_drivers_per_loc_in_sample'] = self.__dct_max_n_drivers_per_loc_in_sample

                    return __dct_process_dict_drivers

            self.update_log(message=f'There are {len(
                self.__dict_driver_tour_pair_variable_cost)} driver-tour combinations in the model.',
                module_name='grb_optimize.py/read_and_optimize')

            self.__set_driver_locs = set(self.__dct_dloc_tours)
            self.__set_tours = set(self.__shift_ctrl_location)

            if OPT_PARAMS.APPLY_MAX_DRIVER_CNT or not self.__dct_max_n_drivers_per_loc_in_sample:
                self.__read_location_params()
            else:
                if OPT_PARAMS.APPLY_MAX_DRIVER_CNT:

                    self.__dct_max_drivers_per_loc = {
                        d: self.__dct_max_n_drivers_per_loc_in_sample.get(d, 0) for d in self.__set_driver_locs}

                    self.__dct_max_drivers_per_loc = {
                        k: v for k, v in self.__dct_max_drivers_per_loc.items() if v > 0}

            if self.__dct_max_drivers_per_loc:
                # If the parameter __apply_max_drivers_per_loc is set to False, then all locations specified in
                # __set_locs_to_allow_extra_drivers is allowed to take on drivers

                self.__set_locs_to_allow_extra_drivers = set(
                    [dloc for dloc in self.__set_locs_to_allow_extra_drivers if dloc in set(
                        self.__dct_max_drivers_per_loc)]
                )

            for loccode in self.__list_locations_excluded_from_opt:

                tours = self.__dct_dloc_tours.pop(loccode, [])
                if tours:
                    self.update_log(
                        message=f'There were {len(tours)} tours assigned to {
                            loccode} which is removed due to scn constraint.',
                        module_name='grb_optimize.py/read_and_optimize')

                if loccode in self.__set_locs_to_allow_extra_drivers:
                    self.__set_locs_to_allow_extra_drivers.remove(loccode)

            self.update_log(message='Processing optimization data finished successfully.',
                            module_name='grb_optimize.py/read_and_optimize')

        except Exception as ini_err:

            msg = self.print_exception() + ': ' + str(ini_err)
            self.update_log(message='Optimization initialization failed!. See the error: {}'.format(msg),
                            module_name='grb_optimize.py')

            self.__status = 0
            self.__optimal_tours = {}

        if self.__status == 1:
            return self.__create_model_solve()

    # Create a MIP model

    def __create_model_solve(self):

        try:

            self.__dct_driver_locs_employed_fixed_cost = {d: 200 for d in self.__set_driver_locs}
            self.__dct_driver_locs_subco_fixed_cost = {d: 550 for d in self.__set_driver_locs}

            self.update_log(message='Building driver optimization model ...',
                            module_name='grb_optimize.py/__create_model_solve')

            self.__tourModel = grb_Model(name='DriverOptimization')

            n_movs = len(self.__dct_movement_tours)
            n_driver_locs = len(self.__set_driver_locs)

            self.update_log(
                message=f'Declaring variables and parameters for {n_movs} loaded movements and {n_driver_locs} driver locs ...',
                module_name='grb_optimize.py/__create_model_solve')

            # Decision variables
            var_V_Movement = self.__tourModel.addVars(
                set(self.__dct_movement_tours),
                name="var_V_Movement",
                vtype=GRB.BINARY)
            
            var_Y_tours = self.__tourModel.addVars(
                self.__set_tours,
                name="var_Tours",
                vtype=GRB.BINARY)

            var_employed_per_loc = self.__tourModel.addVars(self.__set_driver_locs,
                                                   name="var_employed_driver",
                                                   vtype=GRB.INTEGER,
                                                   lb=0, ub=1000)

            var_subco_per_loc = self.__tourModel.addVars(self.__set_driver_locs,
                                                   name="var_subco_driver",
                                                   vtype=GRB.INTEGER,
                                                   lb=0, ub=1000)

            # A binary variable that indicates whether a driver at location d is assigned to a tour
            var_X_ij = self.__tourModel.addVars(set(self.__dict_driver_tour_pair_variable_cost),
                                                name="var_X_ij", vtype=GRB.BINARY)

            self.update_log(message='Building constraints ...',
                            module_name='grb_optimize.py/__create_model_solve')

            # Constraints
            # Ensures 1-1 relationship between loaded movements and potential optimal tours
            self.__tourModel.addConstrs((grb_quicksum(
                var_Y_tours[shift] for shift in self.__dct_movement_tours[m]) == var_V_Movement[m]
                for m in var_V_Movement), name="MovementsCons")

            # Ensures that a driver is assigned to a tour if the tour is selected
            self.__tourModel.addConstrs(var_X_ij[dloc, shift] == var_Y_tours[shift] 
                                        for dloc in self.__set_driver_locs for shift in self.__dct_dloc_tours[dloc])

            # Ensures that the number of drivers assigned to a tour is equal to the number of drivers available at dloc
            self.__tourModel.addConstrs(
                (grb_quicksum(var_X_ij[dloc, shift] 
                              for shift in self.__dct_dloc_tours[dloc]) == var_employed_per_loc[dloc] + var_subco_per_loc[dloc] 
                              for dloc in self.__set_driver_locs),
                              name="D2TCons_Employed_subco")
            
            # Management of the number of employed drivers per location
            if self.__dct_employed_drivers_per_loc:

                set_locs_with_employed_drivers = set(self.__dct_employed_drivers_per_loc)

                if not OPT_PARAMS.SCHEDULE_EMPLOYED_FLAG or self.__relax_loc_employed_driver_cnt_cons:
                    # Upper bound constrained on the number of EMPLOYED drivers that can be assigned to a tour per location
                    # Always bounded from the top. Employed drivers can only be reduced. If extra drivers are required, then the 
                    # module will add a new resource from subco
                    self.__tourModel.addConstrs((var_employed_per_loc[d] <= self.__dct_employed_drivers_per_loc[d]
                        for d in set_locs_with_employed_drivers),
                        name="EmployedDriverUpperBound")
                else:
                    self.__tourModel.addConstrs(
                        (var_employed_per_loc[d] == self.__dct_employed_drivers_per_loc[d] for d in set_locs_with_employed_drivers),
                        name="D2TCons_maxEmployedPerLoc")


                del set_locs_with_employed_drivers

            if self.__dct_max_drivers_per_loc:

                # Upper bound constrained on the number of drivers that can be assigned to a tour per location
                __set_driver_locs1 = [
                    x for x in self.__set_driver_locs if x in self.__dct_max_drivers_per_loc]

                if self.__relax_loc_driver_cnt_cons:

                    __set_driver_locs_xtra_drivers_allowed = [
                        x for x in __set_driver_locs1 if x in self.__set_locs_to_allow_extra_drivers]

                    __set_driver_locs_no_xtra_allowed = [
                        x for x in __set_driver_locs1 if x not in __set_driver_locs_xtra_drivers_allowed]

                    if self.__consider_locs_with_not_allowed_drivers:

                        __set_driver_locs_xtra_drivers_allowed.extend(__set_driver_locs_no_xtra_allowed)
                        __set_driver_locs_xtra_drivers_allowed = list(
                            set(__set_driver_locs_xtra_drivers_allowed))
                        __set_driver_locs_no_xtra_allowed = []


                    var_d_i = self.__tourModel.addVars(__set_driver_locs_xtra_drivers_allowed,
                                                    lb=0, name="var_d_i", vtype='I')

                    # Set of driver locations which allow adding extra drivers, e.g., stations and hubs
                    if __set_driver_locs_xtra_drivers_allowed:

                        self.__tourModel.addConstrs((var_employed_per_loc[d] + var_subco_per_loc[d]
                            <= self.__dct_max_drivers_per_loc[d] + var_d_i[d] for d in __set_driver_locs_xtra_drivers_allowed),
                            name="D2TCons1")

                    if __set_driver_locs_no_xtra_allowed:

                        self.__tourModel.addConstrs((var_employed_per_loc[d] + var_subco_per_loc[d]
                            <= self.__dct_max_drivers_per_loc[d] for d in __set_driver_locs_no_xtra_allowed),
                            name="D2TCons2")

                    del __set_driver_locs_xtra_drivers_allowed, __set_driver_locs_no_xtra_allowed

                else:
                    self.__tourModel.addConstrs((var_employed_per_loc[d] + var_subco_per_loc[d]
                                                <= self.__dct_max_drivers_per_loc[d] for d in __set_driver_locs1),
                                                name="D2TCons")

                del __set_driver_locs1

            obj_expr_fixed_employed = var_employed_per_loc.prod(self.__dct_driver_locs_employed_fixed_cost)
            obj_expr_fixed_subco = var_subco_per_loc.prod(self.__dct_driver_locs_subco_fixed_cost)
            obj_expr_variable_cost = var_Y_tours.prod(self.__dict_shift_variable_cost)

            if self.__relax_movement_constraint:

                self.__tourModel.setObjective(
                    obj_expr_fixed_employed + obj_expr_fixed_subco + obj_expr_variable_cost - var_V_Movement.prod(
                        {m: 1e6 for m in var_V_Movement}), 
                    sense=GRB.MINIMIZE)
            
            else:
                # If user decided to let the module add a new resource if required, then the moduel
                # sets up an equal constraint to make sure all loaded movements are scheduled
                self.__tourModel.addConstr(
                    (grb_quicksum(var_V_Movement[m] for m in var_V_Movement) == len(var_V_Movement)), 
                    name="AllMovsScheduled")

                self.__tourModel.setObjective(
                    obj_expr_fixed_employed + obj_expr_fixed_subco + obj_expr_variable_cost, 
                    sense=GRB.MINIMIZE)

            if self.__tourModel is None:
                raise ValueError('MIP was null.')

            __solver_options = {'NodefileStart': self.__dct_grb_setting.get('NodefileStart', 0.5),
                                'Seed': 2295,
                                # 'WorkLimit': self.__dct_grb_setting.get('WorkLimit', 50000),
                                # 'OutputFlag': self.__dct_grb_setting.get('OutputFlag', 0),
                                'TimeLimit': self.__TimeLimit,
                                'MIPGap': self.__MIPGap,
                                'LogFile': self.__grb_log_file,
                                'LogToConsole': 0}

            for par, val in __solver_options.items():
                self.__tourModel.setParam(par, val)

            dur = ElapsedTime()

            self.update_log(message='Running gurobi; tol: {}; time: {} seconds)...'.format(
                self.__MIPGap, self.__TimeLimit),
                module_name='grb_optimize.py/__create_model_solve')

            self.__tourModel.optimize()

            # GRB.OPTIMAL: The optimization was completed successfully, and an optimal solution was found.
            # GRB.INFEASIBLE: The model is infeasible - there's no solution that satisfies all constraints.
            # GRB.INF_OR_UNBD: The model is either infeasible or unbounded.
            # GRB.UNBOUNDED: The model is unbounded - the objective can improve without limit.
            # GRB.CUTOFF: The search was terminated because the objective value of the best solution found to this point is worse than the specified cutoff.
            # GRB.ITERATION_LIMIT: The search was stopped because the limit on the maximum number of simplex iterations was reached.
            # GRB.NODE_LIMIT: The search was stopped because the limit on the maximum number of branch-and-bound nodes was reached.
            # GRB.TIME_LIMIT: The optimization was stopped because it reached the time limit.
            # GRB.SOLUTION_LIMIT: The search was stopped because a limit on the number of solutions was reached.
            # GRB.INTERRUPTED: The optimization was stopped by the user.
            # GRB.NUMERIC: The optimization was terminated due to unrecoverable numerical difficulties.
            # GRB.SUBOPTIMAL: Unable to reach optimality within numerical tolerances; a sub-optimal solution is available.

            self.update_log(message='Solving MIP ... Done!',
                            module_name='grb_optimize.py/__create_model_solve')

            __grb_logs = []
            with open(self.__grb_log_file, 'r') as grbFile:
                log_lines = grbFile.readlines()
                __grb_logs = [lin.replace('\n', '')
                              for lin in log_lines if len(lin) > 0]

            if __grb_logs:

                __grb_logs.insert(0, f'Fullpath: {self.__grb_log_file}')
                
                with open(self.__optimization_log_file, 'a') as logf:
                    logf.writelines(f"{'\n'.join(__grb_logs)}\n")

            __optimal_found = self.__tourModel.status == GRB.OPTIMAL
            __sol_found = self.__tourModel.SolCount > 0

            self.__clean_up_grbnodes()

            __status_str = f'GRB OPTIMAL: {__optimal_found};'
            __status_str = __status_str + \
                f'\nSol Count: {self.__tourModel.SolCount}'

            __status_str = __status_str + \
                f'\nCreation and solve Runtime: {dur.collapsed_time()}.'

            __status_str = __status_str + \
                f'\nMIP Runtime: {dur.collapsed_minutes(
                    self.__tourModel.Runtime)};'

            __status_str = __status_str + \
                '\nIs multi-objective: {};'.format(
                    self.__tourModel.IsMultiObj == 1)

            self.update_log(message=__status_str,
                            module_name='grb_optimize.py/__create_model_solve')

            if __optimal_found or __sol_found:

                self.update_log(message='Processing optimal drivers output ...',
                                module_name='grb_optimize.py/__create_model_solve')

                __set_final_tours = set(
                    [shift_name for shift_name in var_Y_tours if var_Y_tours[shift_name].X > 0])

                self.__set_optimized_input_movements = set(
                    [m for m in var_V_Movement if var_V_Movement[m].X > 0])

                __missing_input_movements = set(
                    [m for m in self.__set_loaded_movements if m not in self.__set_optimized_input_movements])

                # Calculate the total number of employed drivers
                total_employed_drivers = sum(var_employed_per_loc[dloc].X for dloc in self.__set_driver_locs)

                # Calculate the total number of subco drivers
                total_subco_drivers = sum(var_subco_per_loc[dloc].X for dloc in self.__set_driver_locs)


                if len(__missing_input_movements) > 0:  # and self.__all_inpt_OK_check

                    # self.__status = 0
                    self.update_log(
                        message='WARNNING! {} input movements did not appear in the optimal set.'.format(
                            len(__missing_input_movements)),
                        module_name='grb_optimize.py/__create_model_solve')

                if not __set_final_tours or not self.__set_optimized_input_movements:
                    self.__status = 0
                    self.update_log(
                        message='WARNNING! The optimal tours/movements {}/{} set is empty!.'.format(
                            len(__set_final_tours), len(self.__set_optimized_input_movements)
                        ),
                        module_name='grb_optimize.py/__create_model_solve')

                if self.__status == 1:

                    if self.__dict_tours:
                            
                        dct_loc_shft_cntr = {dloc: 1000 for dloc in self.__set_driver_locs}
                        def _get_shift_id(dloc):
                            dct_loc_shft_cntr[dloc] += 1
                            return dct_loc_shft_cntr[dloc]

                        new_shift_id = DriversInfo.get_new_id()

                        for shiftname in __set_final_tours:

                            dloc = self.__shift_ctrl_location[shiftname]
                            new_shiftname = f"{dloc}.S{_get_shift_id(dloc)}"

                            dct_tour = self.__dict_tours.pop(shiftname)

                            self.__dct_loc_driver_count[
                                dloc] = self.__dct_loc_driver_count.get(dloc, 0) + 1

                            dct_tour.update(
                                {'driver': new_shiftname,
                                'shiftname': new_shiftname,
                                'is_fixed': False,
                                'shift_id': new_shift_id,
                                'weekday': 'Mon'})

                            self.__optimal_tours.update(
                                {new_shift_id: DctTour(**dct_tour)})
                            
                            new_shift_id += 1
                    else:
                        self.__optimal_tours = {}
                        return

                    self.__status = 1
                else:
                    self.__optimal_tours = {}

                message = 'Optimal tours/drivers: {};\n'.format(
                    len(self.__optimal_tours.keys()))

                if self.__status == 1:

                    message = message + \
                        '{} out of {} input movements were planned ({}%);'.format(
                            len(self.__set_optimized_input_movements),
                            len(self.__set_loaded_movements),
                            round(100 * len(self.__set_optimized_input_movements)/len(
                                self.__set_loaded_movements), 1))

                    message = message + f"\nTotal employed drivers: {total_employed_drivers};"
                    message = message + f"\nTotal subco drivers: {total_subco_drivers};"

                self.update_log(message=message,
                                module_name='grb_optimize.py/__create_model_solve')

            else:

                if self.__tourModel.status == GRB.INFEASIBLE:
                    __m_status = 'INFEASIBLE'
                elif self.__tourModel.status == GRB.INF_OR_UNBD:
                    __m_status = 'INF_OR_UNBD'
                elif self.__tourModel.status == GRB.UNBOUNDED:
                    __m_status = 'UNBOUNDED'
                else:
                    __m_status = str(self.__tourModel.status)

                __message = f'Module status: {
                    __m_status}. Relaxing some constraints ...; '
                self.update_log(message=__message,
                                module_name='grb_optimize.py/__create_model_solve')

                if not self.__retry_optimization():
                    self.__optimal_tours = {}

        except Exception:
            self.update_log(message='Optimization failed!: {}'.format(self.print_exception(False)),
                            module_name='grb_optimize.py')

            self.__status = 0

            self.__optimal_tours = {}

    def __retry_optimization(self):

        if self.__dct_max_drivers_per_loc:

            if not self.__relax_loc_driver_cnt_cons:

                
                self.update_log(message='Retrying optimization by adding extra drivers in some locations ...',
                                module_name='grb_optimize.py/__retry_optimization')

                self.__relax_loc_driver_cnt_cons = True

                self.__create_model_solve()
                return True
            
            if not self.__consider_locs_with_not_allowed_drivers:

                self.update_log(
                    message='Retrying optimization by adding extra drivers in some locations where it was not allowed ...',
                    module_name='grb_optimize.py/__retry_optimization')

                self.__consider_locs_with_not_allowed_drivers=True
                self.__create_model_solve()
                return True

            if OPT_PARAMS.SCHEDULE_EMPLOYED_FLAG and not self.__relax_loc_employed_driver_cnt_cons:

                self.update_log(
                    message='Retrying optimization by adding extra drivers in some locations where it was not allowed ...',
                    module_name='grb_optimize.py/__retry_optimization')

                self.__relax_loc_employed_driver_cnt_cons=True
                self.__create_model_solve()
                return True

            if not self.__relax_movement_constraint:
                self.__relax_movement_constraint = True

                self.update_log(
                    message='Retrying optimization by relaxing movements constraint; tries to maximize number of scheduled movements ...',
                    module_name='grb_optimize.py/__retry_optimization')

                self.__create_model_solve()
                return True

        else:
            if not self.__relax_movement_constraint:
                self.__relax_movement_constraint = True

                self.update_log(
                    message='Retrying optimization by relaxing movements constraint; tries to maximize number of scheduled movements ...',
                    module_name='grb_optimize.py/__retry_optimization')

                self.__create_model_solve()
                return True

        return False

    def update_log(self, message, module_name='grb_optimize.py'):

        message = f"{module_name}|{message}"
        LogEntry.log_entry(message=message)

        message = datetime.now().strftime('%Y-%m%d %I:%M') + f'|{message}'

        display_in_console(message)
        
        with open(self.__optimization_log_file, 'a', errors="ignore", encoding="utf8") as f1:
            f1.writelines('\n' + message)

    def print_exception(self):

        try:

            exc_type, exc_obj, tb = exc_info()
            f = tb.tb_frame
            lineno = tb.tb_lineno
            filename = f.f_code.co_filename
            checkcache(filename)
            line = getline(filename, lineno, f.f_globals)

            message = '({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

            LogEntry.log_entry(message=message, level='ERROR')
            return message

        except Exception as err:
            LogEntry.log_entry(message=str(err), level='ERROR')
            return str(err)

    def __clean_up_grbnodes(self):

        try:
            lst_dirs = listdir()
            grb_nodes_dirs = [
                x for x in lst_dirs if 'grbnodes' in path.basename(x).lower()]

            while grb_nodes_dirs:
                rmtree(grb_nodes_dirs.pop())

        except Exception as err:
            return str(err)

    def load_external_grb_data(self, input_file_name):
        """
        For remote run only
        """

        __dct_process_dict_drivers = load_obj(
            str_FileName=input_file_name, path=LION_OPTIMIZATION_PATH)

        if __dct_process_dict_drivers:

            self.__dct_external_grb_data = Dict2Class(
                __dct_process_dict_drivers)

            self.__set_all_driver_locs = self.__dct_external_grb_data.set_all_driver_locs
            self.__dict_driver_tour_pair_variable_cost = self.__dct_external_grb_data.dict_driver_tour_pair_cost
            self.__set_loaded_movements = self.__dct_external_grb_data.set_loaded_movements
            self.__dct_max_n_drivers_per_loc_in_sample = self.__dct_external_grb_data.dct_max_n_drivers_per_loc_in_sample

            return self.__dct_external_grb_data.grb_output_file
