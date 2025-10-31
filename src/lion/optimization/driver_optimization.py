from collections import defaultdict
from copy import deepcopy
from lion.config.paths import LION_OPTIMIZATION_PATH
from lion.optimization.opt_params import OPT_PARAMS
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.utils.order_dict_by_value import order_dict_by_value
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.ui.ui_params import UI_PARAMS
from pandas import DataFrame
import gc
from sqlalchemy import case, update
from lion.orm.location import Location
from lion.shift_data.add_driver_loc import ADD_DRIVER
from sqlalchemy.exc import SQLAlchemyError
from lion.orm.drivers_info import DriversInfo
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.orm.operators import Operator
from lion.utils.monitor_memory import monitor_memory_usage
from lion.logger.status_logger import log_message
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER
from lion.utils.safe_copy import secure_copy
from lion.utils.split_list import split_list
from lion.graph.build_connections import CONNECTION_TREE
from lion.optimization.solver import SolveMIP
from lion.algorithms.depth_first_search import DEPTH_FIRST_SEARCH
from lion.optimization.gurobi.gurobi_input_data import GUROBI_INPUT_DATA
from os import path as os_path
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from time import sleep


class DriverOptimization():

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance
    
    def __init__(self):
        pass

    def initialize(self):

        try:
            
            self.__dct_recommended_movements_per_driver_loc = {}
            self.__dct_optimal_tours_with_drivers = {}
            self.__dct_loc_types = Location.location_types()

            if not UI_MOVEMENTS.dict_all_movements:
                raise Exception('No new movement data was provided!')

            GUROBI_INPUT_DATA.reset()
            ADD_DRIVER.reset()
            CONNECTION_TREE.reset()
            DEPTH_FIRST_SEARCH.reset()

            ADD_DRIVER.xcption_logger = OPT_LOGGER
            DEPTH_FIRST_SEARCH.xcption_logger = OPT_LOGGER
            CONNECTION_TREE.xcption_logger = OPT_LOGGER

            self._initialized = True

        except Exception:
            self._initialized = False
            OPT_LOGGER.log_exception('Initializing DriverOptimization failed!')

        return self._initialized

    def reset(self):
        self._initialized = False

    @classmethod
    def get_instance(cls):
        return cls()
    
    def initialize_and_run(self):

        if not self.initialize():
            return False

        OPT_LOGGER.log_info(
            message=f"Optimization process started with {len(OPT_PARAMS.DCT_MOVEMENTS_TO_OPTIMIZE)} loaded movements. ")

        self.__dct_recommended_movements_per_driver_loc = OPT_PARAMS.DCT_RECOMMENDED_MOVEMENTS_PER_DRIVER_LOC
        
        self.__dct_optimal_tours_with_drivers = {}
        self.__dict_constructed_tours_with_drivers = {}
        self.__dct_loc_recommended_movements_temp = defaultdict(set)

        self._maximum_waiting_minutes = UI_PARAMS.MAXIMUM_DOWNTIME
        self._maxreposmin = UI_PARAMS.MAX_REPOS_DRIV_MIN
        self._dblman_shift_dur = UI_PARAMS.DOUBLE_MAN_SHIFT_DUR

        self._maxcontime_default, self._maxreposdrivmin_default = OPT_PARAMS.MAXDOWNTIME_MAXREPOSMIN

        __grb_setting_message = 'Here are applied optimization params:'
        status_params = f"MAXIMUM_DOWNTIME: {UI_PARAMS.MAXIMUM_DOWNTIME}, \n" + \
            f"MAX_REPOS_DRIV_MIN: {UI_PARAMS.MAX_REPOS_DRIV_MIN}, \n" + \
                f"DOUBLE_MAN_SHIFT_DUR: {UI_PARAMS.DOUBLE_MAN_SHIFT_DUR}"

        OPT_LOGGER.log_info(message=f"{__grb_setting_message}\n{status_params}")

        try:

            if self.__dct_recommended_movements_per_driver_loc:

                rebuild_executed = False
                self.__set_movs_with_feas_shift = set()

                while True:

                    STATUS_CONTROLLER.reset()

                    __driver_locs = list(self.__dct_recommended_movements_per_driver_loc)

                    __dct_driver_locs_pairs = {
                        lc: len(self.__dct_recommended_movements_per_driver_loc[lc]) for lc in __driver_locs}

                    for m in [mv for mv in OPT_PARAMS.SETOF_DOUBLEMAN_MOVEMENTS 
                              if mv not in self.__set_movs_with_feas_shift]:

                        loc_code = UI_MOVEMENTS.dict_all_movements[m]['From']
                        if self.__dct_loc_types[loc_code].lower() != 'customer':
                            self.__dct_recommended_movements_per_driver_loc.setdefault(loc_code, set()).add(m)

                        loc_code = UI_MOVEMENTS.dict_all_movements[m]['To']
                        if self.__dct_loc_types[loc_code].lower() != 'customer':
                            self.__dct_recommended_movements_per_driver_loc.setdefault(loc_code, set()).add(m)

                    __dct_driver_locs_pairs = order_dict_by_value(
                        dct=__dct_driver_locs_pairs, asc=False)

                    __driver_locs = list(__dct_driver_locs_pairs)
                    del __dct_driver_locs_pairs

                    cntr = 0
                    n_location_options = len(__driver_locs)
                    
                    OPT_LOGGER.log_statusbar(f'Building tours for {n_location_options} locations ...')
                    
                    while __driver_locs:

                        cntr += 1
                        driverloc = __driver_locs.pop()

                        try:
                            recommended_movements = self.__dct_recommended_movements_per_driver_loc.pop(
                                driverloc)

                            driverloc = driverloc.split('.')[0]

                            # Separate double-man and regular movements
                            double_man_movements = set(recommended_movements) & OPT_PARAMS.SETOF_DOUBLEMAN_MOVEMENTS
                            regular_movements = set(recommended_movements) - double_man_movements

                            _double_man_movements = list(double_man_movements)
                            _regular_movements = list(regular_movements)

                            self.__preprocess_movements_before_tour_construction(
                                list_m=_regular_movements.copy(), driver_loc=driverloc)
                            
                            if OPT_PARAMS.SCHEDULE_DBLMAN_MOVS:

                                self.__preprocess_movements_before_tour_construction(
                                    list_m=_double_man_movements.copy(),
                                    driver_loc=driverloc, 
                                    double_man=True)
                        
                        except Exception:
                            log_message(f'{driverloc} generated an exception: {OPT_LOGGER.log_exception(popup=False)}')
                            return False
                        
                        STATUS_CONTROLLER.update_status_progress(cntr, n_location_options)

                    OPT_LOGGER.log_statusbar(
                        f'Consolidating intermediate tours (Round {int(rebuild_executed) + 1})...') 

                    ADD_DRIVER.consolidate_dict_tours_with_drivers(consolidate_all=rebuild_executed)
                    _add_drivers_dict_tours_with_drivers = secure_copy(ADD_DRIVER.dict_tours_with_drivers)

                    [self.__set_movs_with_feas_shift.update(v['list_loaded_movements']) 
                        for v in _add_drivers_dict_tours_with_drivers.values()]

                    _list_not_scheduled_movs = [m for m in OPT_PARAMS.SETOF_MOVEMENTS_IN_SCOPE 
                                                if m not in self.__set_movs_with_feas_shift]

                    if not _list_not_scheduled_movs or rebuild_executed:

                        self.__dict_constructed_tours_with_drivers.update(_add_drivers_dict_tours_with_drivers)
                        ADD_DRIVER.dict_tours_with_drivers = {}
                        break
                    
                    else:
                        rebuild_executed = True

                        ADD_DRIVER.dict_tours_with_drivers = {}

                        OPT_LOGGER.log_info(f'ReBuilding tours for {len(_list_not_scheduled_movs)} movements ...') 
                        
                        for m in _list_not_scheduled_movs:

                            locFrom = UI_MOVEMENTS.dict_all_movements[m]['From']
                            locTo = UI_MOVEMENTS.dict_all_movements[m]['To']

                            if self.__dct_loc_types[locFrom].lower() != 'customer':
                                self.__dct_loc_recommended_movements_temp[f"{locFrom}.Temp"].update([m])

                            if self.__dct_loc_types[locTo].lower() != 'customer':
                                self.__dct_loc_recommended_movements_temp[f"{locTo}.Temp"].update([m])

                        self.__dct_recommended_movements_per_driver_loc = {}
                        self.__dct_recommended_movements_per_driver_loc.update(dict(
                            self.__dct_loc_recommended_movements_temp))
                        
                        df_mov_cnt = DataFrame([{
                            'loc_code': k, 
                            'n_movements': len(v),
                            'movements': '|'.join([str(m) for m in v])} 
                            for k, v in self.__dct_recommended_movements_per_driver_loc.items()]
                        )
                        
                        df_mov_cnt.to_csv(os_path.join(
                            LION_OPTIMIZATION_PATH, 'NumberOfAllocatedMovementsPerDriverLocII.csv'), index=False)

                # Enf of while loop

                STATUS_CONTROLLER.reset()

                if not self.__dict_constructed_tours_with_drivers:
                    OPT_LOGGER.log_info(
                        'No tour-driver combination was built!')

                    raise Exception('No tour-driver combination was built!')

                [self.__set_movs_with_feas_shift.update(v['list_loaded_movements']) 
                for v in self.__dict_constructed_tours_with_drivers.values()]

                _list_not_scheduled_movs = [m for m in OPT_PARAMS.SETOF_MOVEMENTS_IN_SCOPE 
                                            if m not in self.__set_movs_with_feas_shift]

                if _list_not_scheduled_movs:

                    lanes = [[m, UI_MOVEMENTS.dict_all_movements[m].loc_string, UI_MOVEMENTS.dict_all_movements[m]['DrivingTime']]
                                for m in _list_not_scheduled_movs]

                    df = DataFrame(lanes, columns=['movement_id' ,'loc_string', 'driving_time'])
                    df.to_csv(os_path.join(
                            LION_OPTIMIZATION_PATH, 'MovementsWithNoFeasTour.csv'), index=False)
                    
                    OPT_LOGGER.log_info(
                        f"\nNOTE: There are {len(_list_not_scheduled_movs)} movements with no associated feasible tours!")

                    del df

            OPT_LOGGER.log_statusbar('Running optimization ...')

            if self.__optimize_drivers():
                self.__dct_optimal_tours_with_drivers = self.__grb_output.optimal_tours
            else:
                self.__dct_optimal_tours_with_drivers = {}

            return self.__dct_optimal_tours_with_drivers and self.save_optimal_schedule()

        except Exception:
            OPT_LOGGER.log_exception(popup=False, remarks='Read and generate failed!')

        return False

    def __preprocess_movements_before_tour_construction(self, list_m=[], driver_loc='', double_man=False):

        if not list_m or not driver_loc:
            return

        max_dblman_runtime = 0
        if double_man:
            max_dblman_runtime = max([UI_MOVEMENTS.dict_all_movements[m]['DrivingTime'] for m in list_m])

        try:
            
            init_category_length = 90
            n_all_movs = len(list_m)

            movements_bucket_list = split_list(
                input_list=list_m,
                category_length=init_category_length)
            
            bucket_cntr = 0
            while movements_bucket_list:

                bucket_cntr += 1
                
                monitor_memory_usage()
                list_m = movements_bucket_list.pop(0)

                n_movs = len(list_m)


                if UI_PARAMS.MEMORY_USAGE > 97:

                    OPT_LOGGER.log_info(message=f"WARRNING: Memory usage is at {UI_PARAMS.MEMORY_USAGE}%." + \
                                        " Params have been adjusted. Gaurbage collection and sleep 5 sec.")
                    
                    gc.collect()
                    sleep(5)

                    UI_PARAMS.MAXIMUM_DOWNTIME = min(60, int(0.8 * UI_PARAMS.MAXIMUM_DOWNTIME))
                    UI_PARAMS.MAX_REPOS_DRIV_MIN = min(60, int(0.8 * UI_PARAMS.MAX_REPOS_DRIV_MIN))

                elif n_movs >= init_category_length:
                    UI_PARAMS.MAXIMUM_DOWNTIME = self._maxcontime_default
                    UI_PARAMS.MAX_REPOS_DRIV_MIN = self._maxreposdrivmin_default

                elif n_movs >= 60:
                    UI_PARAMS.MAXIMUM_DOWNTIME = self._maximum_waiting_minutes
                    UI_PARAMS.MAX_REPOS_DRIV_MIN = self._maxreposmin

                elif n_movs >= 30:
                    UI_PARAMS.MAXIMUM_DOWNTIME = 240
                    UI_PARAMS.MAX_REPOS_DRIV_MIN = 270

                else:
                    UI_PARAMS.MAXIMUM_DOWNTIME = 360
                    UI_PARAMS.MAX_REPOS_DRIV_MIN = 270

                if max_dblman_runtime:
                    UI_PARAMS.MAX_REPOS_DRIV_MIN = max_dblman_runtime + 30
                    UI_PARAMS.DOUBLE_MAN_SHIFT_DUR = max(self._dblman_shift_dur, int(2 * max_dblman_runtime) + 90)

                utilized_params_and_ram = f"Empty: {UI_PARAMS.MAX_REPOS_DRIV_MIN } DownTime: {UI_PARAMS.MAXIMUM_DOWNTIME}"
                utilized_params_and_ram = f"{utilized_params_and_ram} RAM: {UI_PARAMS.MEMORY_USAGE} %"

                OPT_LOGGER.log_statusbar(
                    f'Processing {driver_loc} bucket {bucket_cntr}. Total {driver_loc} movements: {n_all_movs}. ' + \
                         f'Params: {utilized_params_and_ram} ...')

                self.__construct_tours_with_driver(
                    set_loaded_movements=set(list_m),
                    driver_locs=[driver_loc],
                    double_man=double_man)

        except Exception:
            OPT_LOGGER.log_exception(popup=False, remarks='preprocessing movements before tour cosntruction failed!')


    def __construct_tours_with_driver(self, driver_locs=[], set_loaded_movements=set(), double_man=False):
        """
            This module construct tours based on all the movements recommended to a driver loc.
            Thus, only one drive rlocation is evaluated for all tours
        """
        try:

            if not set_loaded_movements or not driver_locs:
                return

            # Construct tours with drivers --------------------------------------
            CONNECTION_TREE.set_input_movements = set_loaded_movements
            CONNECTION_TREE.build_connection_tree()
            DEPTH_FIRST_SEARCH.connection_tree = CONNECTION_TREE
            DEPTH_FIRST_SEARCH.construct_tours(apply_double_man_rules=double_man)

            ADD_DRIVER.add_drivers(dct_tours_data=DEPTH_FIRST_SEARCH.dct_tours_data,
                                   driver_loc=driver_locs[0])

            # Construct tours with drivers End ------------------------------------

        except Exception as err:

            strerr = OPT_LOGGER.log_exception(popup=False)
            log_message(message=strerr,
                       module_name='driver_strategic_optimization.py/__construct_tours_with_driver')

            del err

    def __load_data_for_gurobi(self):

        __dct_grb_input = {}
        try:
            class GrbInput:
                def __init__(self, dct_data={}):
                    for key in dct_data:
                        setattr(self, key, dct_data[key])

            if self.__dict_constructed_tours_with_drivers:
                __dct_grb_input['dict_tours'] = deepcopy(self.__dict_constructed_tours_with_drivers)


        except Exception:
            OPT_LOGGER.log_exception(
                popup=False, remarks='Dumping grb input data failed!')

        if __dct_grb_input:
            self.__dict_constructed_tours_with_drivers = {}
            return GrbInput(__dct_grb_input)

        return None

    def __optimize_drivers(self):

        grb_input_data = self.__load_data_for_gurobi()
        if not grb_input_data:
            return False

        GUROBI_INPUT_DATA.dict_tours = grb_input_data.dict_tours

        self.__grb_output = self.__load_grb_output()
        if self.__grb_output is None:
            return False

        try:
            if not self.__grb_output.optimal_tours:
                raise Exception(
                    'No optimal drivers were reported by the optimizer!')

            return True

        except Exception:
            OPT_LOGGER.log_exception(False)

            return False

    def __load_grb_output(self):

        try:
            __exc_grb = SolveMIP()
            __exc_grb.grb_input_data = GUROBI_INPUT_DATA

            return __exc_grb.grb_output

        except Exception:
            OPT_LOGGER.log_exception(False)

        return None

    def save_optimal_schedule(self):
        """
        Saves changes on local_drivers_info and local_movements
        """

        try:

            if self.update_drivers_info():

                _set_all_loaded_m = set([m for m in UI_MOVEMENTS.dict_all_movements 
                                         if m in OPT_PARAMS.SETOF_MOVEMENTS_IN_SCOPE])

                log_message(f'Saving optimized schedule for {len(_set_all_loaded_m)} loaded movements in scope ...')

                _set_all_m = set(UI_MOVEMENTS.dict_all_movements)

                DriversInfo.save_dct_tours(
                    dct_tours=self.__dct_optimal_tours_with_drivers)

                for shiftid in self.__dct_optimal_tours_with_drivers:

                    dct_optimal_driver = self.__dct_optimal_tours_with_drivers[shiftid]

                    if dct_optimal_driver:

                        _shift_movs = [
                            m for m in dct_optimal_driver.list_movements if m in _set_all_m]

                        list_loaded = [
                            m for m in _shift_movs if UI_MOVEMENTS.dict_all_movements[m].is_loaded()]

                        list_repos = [
                            m for m in _shift_movs if m not in list_loaded]

                        if list_loaded:

                            try:

                                update_cases = case(
                                    {movid: shiftid for movid in list_loaded},
                                    value=ShiftMovementEntry.movement_id
                                )

                                LION_SQLALCHEMY_DB.session.execute(
                                    update(ShiftMovementEntry)
                                    .where(ShiftMovementEntry.movement_id.in_(list_loaded))
                                    .values(shift_id=update_cases)
                                )

                                LION_SQLALCHEMY_DB.session.commit()

                            except SQLAlchemyError as err:
                                LION_SQLALCHEMY_DB.session.rollback()
                                OPT_LOGGER.log_exception(
                                    popup=False, remarks=f'Saving optimal schedule  failed! {str(err)}')

                            except Exception:
                                LION_SQLALCHEMY_DB.session.rollback()
                                OPT_LOGGER.log_exception(
                                    popup=False, remarks='Saving optimal schedule  failed!')

                        if list_repos:

                            _dct_imapcted_movs = {
                                m: UI_MOVEMENTS.dict_all_movements[m] for m in list_repos}

                            for m in list_repos:

                                _dct_m = _dct_imapcted_movs[m]
                                _dct_m.shift_id = shiftid
                                _dct_m.update_str_id()

                                ShiftMovementEntry.add_dct_m(dct_m=_dct_m)

                log_message('Schedule saved successfully!')

                return True

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            OPT_LOGGER.log_exception(
                popup=True, remarks='Saving optimal schedule  failed!')

        return False

    def update_drivers_info(self):

        try:

            __list_drivers = list(self.__dct_optimal_tours_with_drivers)

            log_message(f'Updating optimized drivers for {len(__list_drivers)} shifts ...')

            _all_records = []

            while __list_drivers:

                _shift_id = __list_drivers.pop()

                _shiftname = self.__dct_optimal_tours_with_drivers[_shift_id].shiftname
                _ctrl_loc = _shiftname.split('.')[0].strip()
                _tour_start_loc = self.__dct_optimal_tours_with_drivers[_shift_id].get(
                    'tour_loc_from', _ctrl_loc)

                dct_driver = {
                    'shiftname': _shiftname,
                    'start_loc': _tour_start_loc,
                    'loc': _tour_start_loc,
                    'vehicle': 1,
                    'double_man': False,
                    'ctrl_loc': _ctrl_loc,
                    'home_base': True,
                    'shift_id': _shift_id,
                    'operator': Operator.get_operator_id(operator_name='FedEx Express')}

                driverObj = DriversInfo(**dct_driver)

                for dy in OPT_PARAMS.OPTIMIZATION_WEEKDAYS:
                    setattr(driverObj, dy.lower(), True)

                _all_records.append(driverObj)

            LION_SQLALCHEMY_DB.session.add_all(_all_records)
            LION_SQLALCHEMY_DB.session.commit()

            DriversInfo.refresh_cache()

            return True

        except SQLAlchemyError:
            OPT_LOGGER.log_exception(
                popup=False, remarks='Updating new drivers info failed! {str(err)}')
            LION_SQLALCHEMY_DB.session.rollback()

            return False

        except Exception:
            OPT_LOGGER.log_exception(
                popup=False, remarks='Updating new drivers info failed!')

            LION_SQLALCHEMY_DB.session.rollback()

        return False

DRIVER_OPTIMIZATION = DriverOptimization.get_instance()