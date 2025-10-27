from collections import defaultdict
import logging
from lion.movement.movements_manager import UI_MOVEMENTS
import lion.logger.exception_logger as xcption_logger
from lion.utils.is_loaded import IsLoaded
from lion.ui.ui_params import UI_PARAMS
from lion.orm.user_params import UserParams
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER


class DepthFirstSearch():

    _instance = None

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self):
        pass
    
    def initialize(self, reset=False):

        if not self._initialized:

            try:
                self.__keep_tours_with_all_loaded_movements_only = False
                self.__set_input_movements = set()
                self.__dct_tour_string_val = {}
                self.__max_path_val_default = UserParams.get_param(param='maxtourdur', if_null=720)
                
                self.__apply_double_man_rules = False
                self.__xcption_logger = xcption_logger

                self.__is_loaded = IsLoaded()
                self._initialized = True

            except Exception:
                self._initialized = False
                self.__xcption_logger.log_exception("Initializing DFS failed!")

    def reset(self):

        self._initialized = False
        self.initialize(reset=True)

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
    def keep_tours_with_all_loaded_movements_only(self):
        return self.__keep_tours_with_all_loaded_movements_only

    @keep_tours_with_all_loaded_movements_only.setter
    def keep_tours_with_all_loaded_movements_only(self, x):
        self.__keep_tours_with_all_loaded_movements_only = x

    @property
    def dct_tour_string_val(self):
        return self.__dct_tour_string_val

    @property
    def dct_tours_data(self):
        return dict(self.__dct_tours_data)

    @property
    def set_input_movements(self):
        return self.__set_input_movements

    @set_input_movements.setter
    def set_input_movements(self, set_movements):
        self.__set_input_movements = set_movements

    @property
    def connection_tree(self):
        return self.__connection_tree

    @connection_tree.setter
    def connection_tree(self, contree):

        try:
            self.__connection_tree = contree
            self.__dict_all_movements = UI_MOVEMENTS.dict_all_movements
            self.__set_input_movements = self.__connection_tree.set_input_movements

            __edges_items = [[int(k[0]), int(k[1]), int(v)]
                             for k, v in self.__connection_tree.dict_con_time_extended.items()]

            __graph = defaultdict(dict)

            [__graph[__tuple[0]].update(
                {__tuple[1]: __tuple[2]}) for __tuple in __edges_items]

            self.__graph = dict(__graph)

            self.__nodes = set([x[0] for x in __edges_items])
            self.__nodes.update([x[1] for x in __edges_items])

            __graph_dict_connection_time = defaultdict(dict)

            __edges_items_II = [[int(k[0]), int(k[1]), int(v)]
                                for k, v in self.__connection_tree.dict_connection_time.items()]

            [__graph_dict_connection_time[__tuple[0]].update(
                {__tuple[1]: __tuple[2]}) for __tuple in __edges_items_II]

            self.__graph_dict_connection_time = dict(
                __graph_dict_connection_time)

            del __edges_items, __edges_items_II, __graph_dict_connection_time, __graph

        except Exception:
            self.__xcption_logger.log_exception(popup=False)

    def construct_tours(self, 
                        show_status_bar=False, 
                        apply_double_man_rules=False):

        """
        NOTE: If apply_double_man_rules is enabled, the shift duration parameters will be extended to double as it is now,
        meaning, the tours will be selected whose duration does not exceed 24 hours instead of 12 hours
        """
        try:

            self.__dct_tour_string_val: dict = {}
            self.__apply_double_man_rules = apply_double_man_rules
            self.__double_man_shift_dur = UI_PARAMS.DOUBLE_MAN_SHIFT_DUR
            self.__max_path_val = self.__double_man_shift_dur if apply_double_man_rules else self.__max_path_val_default

            if len(self.__set_input_movements) == 0:
                raise ValueError('Specify a list of loaded movements ...')

            self.__dct_start_tours = defaultdict(dict)

            __dct_loc_movs = defaultdict(list)
            for m in self.__set_input_movements:
                __dct_loc_movs[self.__dict_all_movements[m]['From']].append(m)

            __dct_loc_movs = dict(__dct_loc_movs)

            if show_status_bar:

                STATUS_CONTROLLER.reset()
                _n_all = len(__dct_loc_movs)
                _cntr = 0
                for loc_code in set(__dct_loc_movs):
                    _cntr += 1
                    STATUS_CONTROLLER.update_status_progress(_cntr, _n_all)
                    __movs = __dct_loc_movs[loc_code]

                    while __movs:
                        self.__breadth_first_search(__movs.pop())

                STATUS_CONTROLLER.reset()
            else:
                for loc_code in set(__dct_loc_movs):
                    __movs = __dct_loc_movs[loc_code]
                    while __movs:
                        self.__breadth_first_search(__movs.pop())

            self.__process_generated_tour_strings()

        except Exception:
            self.__xcption_logger.log_exception(
                popup=False, remarks='Exception occured while running construct_tours!')

            STATUS_CONTROLLER.reset()

    def __process_generated_tour_strings(self):

        try:

            if self.__keep_tours_with_all_loaded_movements_only:

                self.__keep_tours_with_all_loaded_movements_only = False
                self.__keep_tours_with_all_loaded()

            self.__postprocessing_tour_strings()

            self.__dct_tours_data = defaultdict(dict)

            for t_str in set(self.__dct_tour_string_orig_dest):

                self.__dct_tours_data.setdefault(t_str, {}).update({
                    'dur': self.__dct_tour_string_val[t_str],
                    'orig': self.__dct_tour_string_orig_dest.get(t_str, {}).get('orig', ''),
                    'dest': self.__dct_tour_string_orig_dest.get(t_str, {}).get('dest', ''),
                    'first_m': self.__dct_tour_string_orig_dest.get(t_str, {}).get('first_m', 0),
                    'last_m': self.__dct_tour_string_orig_dest.get(t_str, {}).get('last_m', 0),
                    'double_man': self.__apply_double_man_rules
                })

        except Exception:
            self.__xcption_logger.log_exception(popup=False)

    def __breadth_first_search(self, start):

        __start_driving_time = self.__dict_all_movements.get(
            start, {}).get('DrivingTime', None)
        
        self.__dct_tour_string_val.update(
                {str(start): __start_driving_time})

        try:

            self.__dct_start_tours[start].update(
                {str(start): __start_driving_time})

            __list_current_strings = [str(start)]

            while __list_current_strings:

                __tour_string = str(__list_current_strings.pop(0))
                __mid = int(__tour_string.split('->').pop())

                __list_outbound_movs = list(
                    self.__graph.get(__mid, {}).keys())

                while __list_outbound_movs:

                    __movement = __list_outbound_movs.pop()

                    if __movement in self.__dct_start_tours:

                        for __t_string in self.__dct_start_tours[__movement]:

                            __dur = self.__dct_tour_string_val[__tour_string] + \
                                self.__dct_tour_string_val[__t_string] + \
                                self.__graph_dict_connection_time[__mid][__movement]

                            if __dur <= self.__max_path_val:
                                
                                __extended_tour_string = f'{__tour_string}->{__t_string}'

                                self.__dct_tour_string_val.update(
                                    {__extended_tour_string: __dur})

                                self.__dct_start_tours[start].update({str(
                                    __extended_tour_string): __dur})

                    else:

                        __dur = self.__dct_tour_string_val[
                            __tour_string] + self.__graph[__mid][__movement]

                        if __dur <= self.__max_path_val:

                            __extended_tour_string = f'{__tour_string}->{__movement}'

                            self.__dct_start_tours[start].update({str(
                                __extended_tour_string): __dur})

                            self.__dct_tour_string_val.update(
                                {__extended_tour_string: __dur})
                            
                            __list_current_strings.append(
                                    str(__extended_tour_string))
                            
        except Exception:
            self.__xcption_logger.log_exception(popup=False)

    def __keep_tours_with_all_loaded(self):

        try:
            __set_tour_strings = set(self.__dct_tour_string_val)
            for tour_string in __set_tour_strings:

                __list_tour_m_string = tour_string.split('->')
                __list_tour_loaded_m = [
                    m for m in __list_tour_m_string if self.__is_loaded.is_loaded(int(m))]

                if len(__list_tour_loaded_m) < len(self.__set_input_movements):
                    self.__dct_tour_string_val.pop(tour_string)

        except Exception:
            self.__xcption_logger.log_exception(popup=False)

    def __postprocessing_tour_strings(self):

        try:
            __set_tour_strings = set(self.__dct_tour_string_val)
        except Exception:
            __set_tour_strings = set()
            self.__xcption_logger.log_exception(popup=False)
        
        self.__dct_tour_string_orig_dest = defaultdict(dict)

        for tour_string in __set_tour_strings:
        
            try:
                if not tour_string:  # Check if tour_string is None or empty
                    continue

                # Split once and reuse the values
                __list_tour_m_string = tour_string.split('->')
                first_m_str = __list_tour_m_string[0]
                last_m_str = __list_tour_m_string[-1]
                dblman = self.__apply_double_man_rules

                first_m = int(first_m_str)
                last_m = int(last_m_str)

                # If the last movement is a repos, skip it
                if self.__dict_all_movements.get(last_m, {}).get(
                    'TrafficType', '').lower() == 'empty':

                    self.__dct_tour_string_val.pop(tour_string)
                    continue

                __t_orig = self.__dict_all_movements[first_m]['From']
                __t_dest = self.__dict_all_movements[last_m]['To']

                self.__dct_tour_string_orig_dest.setdefault(tour_string, {}).update({
                    'first_m': first_m,
                    'last_m': last_m,
                    'orig': __t_orig,
                    'dest': __t_dest,
                    'double_man': dblman
                })

            except ValueError as valrr:
                self.__xcption_logger.log_exception(popup=False, 
                               remarks=f"Value Error occurred when processing {tour_string}: {str(valrr)}")

            except KeyError as keyerr:
                self.__xcption_logger.log_exception(popup=False, 
                               remarks=f"Key Error occurred when processing {tour_string}: {str(keyerr)}")
                
            except Exception:
                self.__xcption_logger.log_exception(popup=False, 
                               remarks=f"Excption occurred when processing {tour_string}")

DEPTH_FIRST_SEARCH = DepthFirstSearch.get_instance()