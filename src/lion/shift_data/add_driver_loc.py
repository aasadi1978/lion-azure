
from collections import defaultdict
from datetime import datetime, timedelta
import gc
from os import listdir
from time import sleep
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER
from lion.tour.tour_analysis import UI_TOUR_ANALYSIS
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.ui.ui_params import UI_PARAMS
from lion.utils.safe_copy import  secure_copy
from lion.utils.dump_obj import dump_obj
from lion.utils.load_obj import load_obj
from lion.utils.empty_dir import empty_dir
import lion.logger.exception_logger as xcption_logger
from lion.orm.drivers_info import DriversInfo
from lion.orm.location import Location
from lion.utils.split_list import split_list
from lion.utils.monitor_memory import monitor_memory_usage
import lion.config.paths as paths
from os.path import basename


class AddDriver():

    _instance=None

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)
            cls._instance.__tour_id = 0

        return cls._instance

    def __init__(self):
        pass

    def _initialize(self):

        self.__ignore_status = False
        if not self.__tour_id:
            self.__tour_id = DriversInfo.get_new_id()

        self.__xcption_logger = xcption_logger
        self.__shift_id = 0
        self.__output_bucket_cntr = 1
        self.__output_dump_bucket_size = 50

        self.__dict_tours_with_drivers = {}
        self.__dict_consolidated_tours_with_drivers = {}
        
        self.__set_loaded_movements = set(
            [m for m, v in UI_MOVEMENTS.dict_all_movements.items() if v.is_loaded()])

        self.__range_dep_times = UI_MOVEMENTS.list_break_min
        self.__dct_footprint = Location.to_dict()

        self.__dct_remarks_per_tour = defaultdict()
        self.initialize_data_dump()

    def reset(self):
        self.__tour_id = 0
        self._initialize()
    
    @property
    def xcption_logger(self):
        return self.__xcption_logger
    
    @xcption_logger.setter
    def xcption_logger(self, x):
        self.__xcption_logger = x

    @classmethod
    def get_instance(cls):
        return cls()

    @property
    def dct_remarks_per_tour(self):
        return self.__dct_remarks_per_tour

    @property
    def dict_tours_with_drivers(self):

        if not self.__dict_tours_with_drivers:
            self.consolidate_dict_tours_with_drivers()

        return self.__dict_tours_with_drivers
    
    @dict_tours_with_drivers.setter
    def dict_tours_with_drivers(self, x):
        self.__dict_tours_with_drivers = x

    def _dump_output(self):

        try:
            dump_obj(obj=self.__dict_consolidated_tours_with_drivers,
                        str_DestFileName=f'DctToursWithDrivers-{datetime.now().strftime(
                            '%Y%m%d %H%M%S')}-{self.__output_dump_bucket_size}-{self.__output_bucket_cntr}.tmp',
                        path=paths.LION_TEMP_OPTIMIZATION_DATA_DUMP_PATH )
            
            self.__dict_consolidated_tours_with_drivers = {}
            self.__output_bucket_cntr += 1
        
        except Exception:
            self.__xcption_logger.log_exception(popup=False, remarks='Dumping feasible tours failed')

    def consolidate_dict_tours_with_drivers(self, consolidate_all=False):

        try:
            tour_datas_files = listdir(paths.LION_TEMP_OPTIMIZATION_DATA_DUMP_PATH)

            if not self.__shift_id:
                self.__dict_tours_with_drivers = {}

            while tour_datas_files:

                try:
                    tfile = tour_datas_files.pop(0)
                    dict_shift_data = load_obj(
                        str_FileName=basename(tfile), path=paths.LION_TEMP_OPTIMIZATION_DATA_DUMP_PATH, if_null={})

                    if dict_shift_data:
                        self.__dict_tours_with_drivers.update(dict_shift_data)

                except Exception:
                    self.__xcption_logger.log_exception(
                        popup=False,
                        remarks=f'consolidate_dict_tours_with_drivers failed for {tfile}! Processing data stopped!')
                    
                    self.__dict_tours_with_drivers = {}
                    break

            else:
                return
            
            if self.__dict_tours_with_drivers and not consolidate_all:

                empty_dir(paths.LION_TEMP_OPTIMIZATION_DATA_DUMP_PATH)

                dump_obj(obj=self.__dict_tours_with_drivers, 
                        str_DestFileName='consolidated_dict_tours_with_drivers.tmp',
                        path=paths.LION_TEMP_OPTIMIZATION_DATA_DUMP_PATH)

            elif self.__dict_tours_with_drivers and consolidate_all:
                empty_dir(paths.LION_TEMP_OPTIMIZATION_DATA_DUMP_PATH)

        except Exception:
            self.__xcption_logger.log_exception(
                popup=False,
                remarks='consolidate_dict_tours_with_drivers failed!')
            
            self.__dict_tours_with_drivers = {}


    def add_drivers(self, **kwargs):
        
        driver_loc = kwargs.get('driver_loc', None)
        dct_tours_data = kwargs.get('dct_tours_data', {})
        self.__shift_id = kwargs.get('shift_id', 0)
        self.__capture_infeas_remarks = kwargs.get('capture_infeas_remarks', False)
        self.__ignore_status = kwargs.get('ignore_status', False)

        if not driver_loc or not dct_tours_data:
            return
        
        try:
            self.__dct_tours_data = {}
            self.__driver_loc = driver_loc
            self.__waive_hbr  = False
            self.__double_man = False
            self.__vehicle_code = 1

            if self.__shift_id:

                if not UI_PARAMS.SHIFT_INFO:
                    return

                driver_home_base, double_man, vehicle = UI_PARAMS.SHIFT_INFO.split(';')
                self.__waive_hbr = not(driver_home_base == 'True')
                self.__double_man = str(double_man) == 'True'
                self.__vehicle_code = int(vehicle)

                UI_PARAMS.SHIFT_INFO = ''

            if dct_tours_data:

                __list_tour_string = list(dct_tours_data)
                self.__dct_tours_data = secure_copy(dct_tours_data)

                dct_tours_data = {}
                n_tour_strings = len(__list_tour_string)

                if n_tour_strings <= self.__output_dump_bucket_size:

                    while __list_tour_string:
                        self.__add_driver_movements(
                            tour_movement_string=__list_tour_string.pop(0))
                    
                    if self.__shift_id:
                        self.__dict_tours_with_drivers.update(self.__dict_consolidated_tours_with_drivers)
                        self.__dict_consolidated_tours_with_drivers = {}
                    else:
                        self._dump_output()

                else:

                    tours_bucket_list = split_list(
                        input_list=__list_tour_string, category_length=self.__output_dump_bucket_size)
                    
                    del __list_tour_string

                    while tours_bucket_list:

                        try:
                            __tmp_list_tour_string = tours_bucket_list.pop(0)
                            
                            if self.__log_memory_usage() >= 97:
                                gc.collect()
                                sleep(5)

                            while __tmp_list_tour_string:

                                try:
                                    self.__add_driver_movements(
                                        tour_movement_string=__tmp_list_tour_string.pop(0))

                                except Exception:
                                    self.__xcption_logger.log_exception(popup=False)
                            
                            self._dump_output()

                        except Exception:
                            self.__xcption_logger.log_exception(
                                popup=False,
                                remarks=f'Adding drivers to tours failed at counter {self.__output_bucket_cntr}!')

            else:
                self.__xcption_logger.write_log_entry(f"No tour has been provided for {self.__driver_loc}")

        except Exception:
            self.__xcption_logger.log_exception(
                popup=False,
                remarks='Adding drivers to tours failed!')

            return

    def __add_driver_movements(self, tour_movement_string=''):
        """
        This module evaluates adding a driver, based in a driver location specified through ``self.__driver_loc`` argument,
        to the tour string provided via the global attribute ``__tour_movement_string_original``. It is called by the public
        method ``add_driver_loc_to_tour_string``.
        """

        try:
            self.__tour_movement_string_original = tour_movement_string

            self.__first_m = self.__dct_tours_data[tour_movement_string]['first_m']
            self.__last_m = self.__dct_tours_data[tour_movement_string]['last_m']

            self.__t_orig = self.__dct_tours_data[tour_movement_string]['orig']
            self.__t_dest = self.__dct_tours_data[tour_movement_string]['dest']
            self.__t_dblman = self.__double_man or self.__dct_tours_data[tour_movement_string].get(
                'double_man', False)

        except Exception:
            self.__xcption_logger.log_exception(
                popup=False,
                remarks=f'processing tour_string {tour_movement_string} for add_driver_movements failed!')
            
            return False


        try:
            self.__tour_movement_string = f"{self.__tour_movement_string_original}"

            self.__remove_first_movement_of_tour_string()
            self.__remove_last_movement_of_tour_string()

            if not self.__tour_movement_string:
                return False

            if self.__driver_loc == self.__t_orig:
                return self.__add_last_driver_mov()
    
            else:

                self.__tour_movement_string = '500000->' + self.__tour_movement_string
                for __idle_minutes in self.__range_dep_times:

                    self.__remove_first_movement_of_tour_string()
                    __turnaround_time = self.__dct_footprint[self.__t_orig]['turnaround_min']

                    __con_time = __turnaround_time + __idle_minutes

                    dct_m_driver_to_orig = UI_MOVEMENTS.get_dct_arriving_movement(
                        orig=self.__driver_loc,
                        dest=self.__t_orig,
                        ArrDateTime=UI_MOVEMENTS.dict_all_movements[
                            self.__first_m]['DepDateTime'] - timedelta(minutes=__con_time))
                    
                    if dct_m_driver_to_orig:

                        self.__tour_movement_string = str(
                            dct_m_driver_to_orig['MovementID']) + '->' + self.__tour_movement_string

                        if self.__add_last_driver_mov():
                            return True
                
                return False

        except Exception:
            self.__xcption_logger.log_exception(
                popup=False,
                remarks=f'__add_driver_movements failed for {self.__driver_loc}!')
            
        return False

    def __add_last_driver_mov(self):

        try:
            __status = 0

            if Location.is_customer(self.__t_dest):
                return False

            if self.__waive_hbr or (self.__driver_loc == self.__t_dest):

                __status, __remark, dct_tour = UI_TOUR_ANALYSIS.refresh_tour(
                    shift_id=self.__shift_id,
                    tour_movement_string=self.__tour_movement_string,
                    ignore_status=self.__ignore_status,
                    capture_infeas_remarks=self.__capture_infeas_remarks,
                    double_man=self.__t_dblman,
                    vehicle=self.__vehicle_code
                )

                if dct_tour:

                    dct_tour.update({'driver': self.__driver_loc,
                                     'tour_id': self.__tour_id,
                                     'double_man': self.__t_dblman,
                                     'vehicle': self.__vehicle_code})

                    dct_tour = UI_TOUR_ANALYSIS.calculate_cost(dct_tour)

                    self.__dict_consolidated_tours_with_drivers.update(
                        {f"{self.__driver_loc}.{self.__tour_id}": dct_tour})
                    
                    self.__tour_id += 1

                    return True

                elif self.__capture_infeas_remarks:
                    self.__dct_remarks_per_tour[self.__tour_id] = UI_TOUR_ANALYSIS.status_report
                
                return False

            else:

                __turnaround_time = self.__dct_footprint[self.__t_dest]['turnaround_min']

                self.__tour_movement_string = self.__tour_movement_string + '->500000'
                for __idle_minutes in self.__range_dep_times:

                    self.__remove_last_movement_of_tour_string()

                    __con_time = __turnaround_time + __idle_minutes

                    if not UI_MOVEMENTS.dict_all_movements.get(self.__last_m, {}):
                        raise ValueError('%d does not exist.' %
                                         (self.__last_m))

                    dct_m_dest_to_driver = UI_MOVEMENTS.get_dct_departing_movement(
                        orig=self.__t_dest,
                        dest=self.__driver_loc,
                        DepDateTime=UI_MOVEMENTS.dict_all_movements[
                            self.__last_m]['ArrDateTime'] + timedelta(minutes=__con_time))

                    if dct_m_dest_to_driver:

                        self.__tour_movement_string = self.__tour_movement_string + '->' + str(
                            dct_m_dest_to_driver['MovementID'])

                        __status, __remark, dct_tour = UI_TOUR_ANALYSIS.refresh_tour(
                            shift_id=self.__shift_id,
                            tour_movement_string=self.__tour_movement_string,
                            ignore_status=self.__ignore_status,
                            capture_infeas_remarks=self.__capture_infeas_remarks,
                            double_man=self.__t_dblman,
                            vehicle=self.__vehicle_code
                        )

                        if dct_tour:

                            dct_tour.update({'driver': self.__driver_loc,
                                             'tour_id': self.__tour_id,
                                             'double_man': self.__t_dblman,
                                             'vehicle': self.__vehicle_code})

                            dct_tour = UI_TOUR_ANALYSIS.calculate_cost(
                                dct_tour)
                            
                            self.__dict_consolidated_tours_with_drivers.update(
                                {f"{self.__driver_loc}.{self.__tour_id}": dct_tour})
                            
                            self.__tour_id += 1

                            return True

                        elif self.__capture_infeas_remarks:
                            self.__dct_remarks_per_tour[self.__tour_id] = UI_TOUR_ANALYSIS.status_report

                return False
            
        except Exception:
            self.__xcption_logger.log_exception(
                popup=False,
                remarks='__add_last_driver_mov failed!')

        return __status == 1
    
    def is_loaded(self, m):
        try:
            return m in self.__set_loaded_movements
        except:
            if str(m) in ['', '0', '500000']:
                pass
            else:
                self.__xcption_logger.log_exception(popup=False, remarks=f"Could not verify {m} as loaded or repos.")

            return True
        
    def __remove_last_movement_of_tour_string(self):

        try:
            __ms = self.__tour_movement_string.split('->')

            while __ms and (__ms[-1] == '500000' or not self.is_loaded(int(__ms[-1]))):
                __ms.pop()

            if __ms:
                self.__last_m = int(__ms[-1])
                self.__t_dest = UI_MOVEMENTS.dict_all_movements[self.__last_m]['To']

                self.__tour_movement_string = '->'.join(__ms)
            else:
                self.__tour_movement_string = ''

        except Exception:
            self.__xcption_logger.log_exception(
                popup=False,
                remarks='Removing tour string head empty movement failed!')

    def __remove_first_movement_of_tour_string(self):

        try:
            __ms = self.__tour_movement_string.split('->')

            while __ms and (__ms[0] == '500000' or not self.is_loaded(int(__ms[0]))):
                __ms.pop(0)

            if __ms:
                self.__first_m = int(__ms[0])
                self.__t_orig = UI_MOVEMENTS.dict_all_movements[self.__first_m]['From']

                self.__tour_movement_string = '->'.join(__ms)
            else:
                self.__tour_movement_string = ''

        except Exception:
            self.__xcption_logger.log_exception(
                popup=False,
                remarks='__remove_first_movement_of_tour_string failed!')

    def __log_memory_usage(self):
        try:

            monitor_memory_usage()

            str_info = STATUS_CONTROLLER.PROGRESS_INFO
            str_info.split('RAM:')[0].strip()
            str_info = f"{str_info} RAM: {UI_PARAMS.MEMORY_USAGE}%"
            STATUS_CONTROLLER.PROGRESS_INFO = str_info

            return UI_PARAMS.MEMORY_USAGE

        except Exception:
            self.__xcption_logger.log_exception(popup=False, remarks='Getting memory usage failed!')

            return None

    def initialize_data_dump(self):
        """
        This method initializes and validates the temp data dump directory for storing temporary optimization data.
        """
        try:
            empty_dir(paths.LION_TEMP_OPTIMIZATION_DATA_DUMP_PATH)
        except Exception:
            self.__xcption_logger.log_exception(
                popup=False,
                remarks='initialize_data_dump failed!')

ADD_DRIVER = AddDriver.get_instance()