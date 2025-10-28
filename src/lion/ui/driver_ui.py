from collections import defaultdict
import logging

from lion.config.paths import (LION_CONSOLIDATED_REPORT_PATH, LION_DIAGNOSTICS_PATH, LION_DRIVER_REPORT_DIST_PATH, 
                          LION_LOGS_PATH, LION_LOCAL_DRIVER_REPORT_PATH, LION_OPTIMIZATION_PATH)
from lion.movement.sort_list_movements import are_movements_overlapped
from lion.orm.scenarios import Scenarios
from lion.shift_data.get_shift_proposal import get_shift_proposals
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER
from lion.tour.tour_analysis import UI_TOUR_ANALYSIS
from lion.ui.ui_params import UI_PARAMS
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.ui.basket import basket_shifts
from lion.ui.basket.pre_load_basket_shifts import pre_load_my_shifts_in_basket
from lion.ui.chart import get_chart_data
from lion.ui.filter_tours import apply_filters
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.ui.options import refresh_options
from lion.utils.concat import concat
from lion.utils.session_manager import SESSION_MANAGER
from lion.utils.to_lion_datetime import to_lion_datetime
from lion.utils.safe_copy import secure_copy
from lion.utils.empty_dir import empty_dir
from lion.utils.df2csv import export_dataframe_as_csv
from lion.utils.combine_date_time import combine_date_time
from lion.utils.is_file_updated import is_file_updated
from lion.utils.split_string import split_string
from lion.logger.exception_logger import log_exception
from lion.ui.arrow import Arrow
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.orm.changeover import Changeover
from lion.orm.drivers_info import DriversInfo
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.orm.shift_index import ShiftIndex
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.movement.dct_movement import DictMovement
from lion.tour.dct_tour import DctTour
from lion.orm.resources import Resources
from lion.bootstrap.constants import MOVEMENT_TYPE_COLOR, LOC_STRING_SEPERATOR, WEEKDAYS_NO_SAT, LION_DATES

from lion.utils.dfgroupby import groupby as df_groupby
from lion.shift_data.save import SaveSchedule
from lion.utils.popup_notifier import show_popup, show_error
from lion.reporting.kpi_report import kpi_report
from lion.utils.sqldb import SqlDb

from lion.xl.write_excel import write_excel as xlwriter
from datetime import timedelta, datetime
from lion.orm.location import Location
from lion.orm.user_params import UserParams
from lion.orm.vehicle_type import VehicleType
from lion.orm.operators import Operator
from lion.logger.status_logger import log_message, log_message
from lion.utils.is_loaded import IsLoaded
from os import listdir, path as os_path
from lion.reporting.generate_driver_report import DRIVER_REPORT
from lion.reporting.gen_driver_dep_arr_report import DepArrReport
from lion.shift_data.shift_manager import SHIFT_MANAGER
from pandas import read_csv, DataFrame, read_excel
from cachetools import TTLCache
from sqlalchemy.exc import SQLAlchemyError
from lion.traffic_types.update_traffic_types import update_traffic_types
from lion.vehicle_types.update_vehicle_types import update_vehicle_types

class DriversUI():

    """
    This module is initialised when loading schedule. The module is loaded in ``__main__.py``
    where the object ``DRIVERS_UI`` is initialised as ``DRIVERS_UI =  Drivers()``.
    """

    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance
    
    def __init__(self):
        pass
    
    def initialize(self):

        if not self._initialized:
            self.__initialize()

    def __initialize(self):

        try:
            self._optimization_output_dir = f"{LION_OPTIMIZATION_PATH}"
            self._dct_cached_info = TTLCache(maxsize=100, ttl=300)
            self._dct_cached_optimization_data = TTLCache(maxsize=100, ttl=6 * 60 * 60)
            self._dct_vis_data_footprint = TTLCache(maxsize=1000, ttl=15 * 60)

            self._dct_driver_locs_per_lane = defaultdict(set)
            self._dct_cached_shifts = {}
            self._infeas_shift_ids = set()
            self._dct_cached_movements = {}
            
            self._selected_vehicles = []
            self._excl_dblman = False
            self._set_excluded_shift_ids = set()
            self._utilisation_range = [0, 100]
            self._set_selected_changeovers = set()
            UI_PARAMS.LIST_FILTERED_SHIFT_IDS = []
            self._dep_arr_report_obj = None
            
            self._dct_traffic_type_colors = {}
            UI_PARAMS.HIDE_INFEASIBLE = False
            self._list_deleted_movs = []
            self._list_changed_movs = []
            self.my_shifts_in_basket = []
            self._list_new_movs = []
            self._filtering_wkdays = []
            self._arrow = Arrow()
            self._filtering_loc_codes = []
            self._is_loaded = IsLoaded()
            self._dct_dump_area = {}
            UI_PARAMS.HIDE_FIXED = False
            self._backup_active_shift_data_b4_optimization = None
            
            self._dct_movement_type_colors = MOVEMENT_TYPE_COLOR

            self._egis_scn = UserParams.get_param('runtimes_scenario')
            self._user_display_name = SESSION_MANAGER.get('user_name')

            self._bar_width = [int(x) for x in UserParams.get_param(
                'bar_width', if_null='45;40;35').split(';')]
            
            STATUS_CONTROLLER.PROGRESS_INFO = ''
            STATUS_CONTROLLER.PROGRESS_PERCENTAGE_STR = 0

            self._dct_available_scenarios = Scenarios.get_available_scenarios()

            self._page_size = self.get_user_param(param='page_size', if_null=15)
            
            Location.validate_region()
            UserParams.update(excluded_locs='')
            UI_PARAMS.update(page_size=self._page_size,
                                    utilisation_range=self._utilisation_range)

            UI_PARAMS.configure_network_defaults()
            UI_RUNTIMES_MILEAGES.initialize()

            if not UI_MOVEMENTS.dict_all_movements:
                UI_MOVEMENTS.refresh_movement_id()

            SHIFT_MANAGER.reset()
            self._initialized = True

        except Exception:

            self._initialized = False
            self._display_err(
                f'DnD initialisation error: {log_exception(False)}')

    def reset(self):
        self._initialized = False
        self.__initialize()
    
    @classmethod
    def get_instance(cls):
        return cls()

    def clear_cache(self):
        """
        clean up self._dct_cached_info  and self._dct_cached_optimization_data
        """
        self._dct_cached_info = {}
        self._dct_cached_optimization_data = {}
        UI_PARAMS.clear('dct_cached_info')
        UI_PARAMS.clear('dct_cached_optimization_data')

    def execute_module(self, module_name='', **kwargs):
        """
        Executes any function (method) within ``Drivers`` class under the name specified in ``module_name`` argument.
        This is handy when I try to execute a module through `post` method using ``py2js`` function.
        """

        method = getattr(self, module_name, None)
        try:
            method = getattr(self, module_name, None)
            if method:
                return method(**kwargs)
            else:
                raise Exception(f"No method named '{module_name}' found!")

        except Exception:
            return {'code': 400, 'message': f'execute_module failed!\n{log_exception(False)}'}

    def enable_tour_locstring_sort(self):

        try:
            UI_PARAMS.SORT_BY_TOUR_LOCSTRING = True
            UI_PARAMS.DICT_DRIVERS_PER_PAGE = {}
            UI_PARAMS.LIST_FILTERED_SHIFT_IDS = []
            UI_PARAMS.ALL_WEEK_DRIVERS_FILTERED = []
            UI_SHIFT_DATA.reset()
        except Exception:
            return {'message': f'Sorting by tourLocString failed! {log_exception(False)}'}

        return {}

    def toggle_zoom(self, **dct_params):

        try:
            zoom_on = dct_params.get('zoom_on', False)
            UserParams.update(enable_zoom=zoom_on)

        except Exception:
            log_exception(popup=False)


    def add_a_vehicle(self):
        """
        In order to update vehicle types, add/remove or modify, one has to
        apply relevent changes on 'vehicles.xlsx' file in LION_FILES_PATHdirectory in LION-Shared SharePoint.
        Once changes applied and saved, the corresponding button in LION can be clicked to apply the changes

        Todo: not belong here
        """

        try:
            return update_vehicle_types()
        except Exception:
            return {'code': 400, 'message': log_exception(popup=False)}


    def add_a_traffic_type(self):
        """
        In order to update traffic types, add/remove or modify, one has to
        apply relevent changes on 'traffic_types.xlsx' file in LION_FILES_PATHdirectory in LION-Shared SharePoint.
        Once changes applied and saved, the corresponding button in LION can be clicked to apply the changes

        Note: This is triggered by the 'update_traffic_types' button in the UI. Traffic types are automatically get updated
        when 'traffic_types.xlsx' is updated
        """

        try:
            return update_traffic_types(force_update=True)
        except Exception:
            return {'code': 400, 'message': log_exception(popup=False, remarks='Updating traffic types failed!')}

    def set_number_of_drivers_per_page(self, **dct_params):

        __page_size = dct_params.get('page_size', None)

        try:
            if __page_size is not None:

                self._page_size = __page_size
                UserParams.update(page_size=__page_size)
                UI_PARAMS.PAGE_SIZE = self._page_size

                status = apply_filters()

                if status.get('code', 200) != 400:
                    return get_chart_data(page_num=1)
                else:
                    raise ValueError(status['error'])

        except Exception:
            self._display_err(
                f"set_number_of_drivers_per_page Failed! {log_exception(False)}")

    def set_barwidth(self):
        self._bar_width = [
            int(x) for x in UserParams.get_param('bar_width', if_null='45;40;35').split(';')]
        
        UI_PARAMS.update(bar_width=self._bar_width)

    def generate_kpi_report(self):
        try:
            return kpi_report(dump_as_xl=True)
        except Exception:
            return {'code': 400, 'message': log_exception(
                popup=True, remarks='Generating KPI report failed!')
            }

    def delete_changeovers(self, **dct_params):
        """
        Deletes changeovers from the database based on the provided parameters. The changeovers are removed from the
        local database and the movements associated with the changeovers remain unaffected, except for the loc_string and tu fields.

        Args:
            dct_params: Additional parameters for filtering changeovers.

        Returns:
            None
        """

        try:
            _changeovers = dct_params.get('changeovers', [])
            if _changeovers:
                _changeovers = [x.split('(')[0].strip() for x in _changeovers]


            deleted_count = len(set(_changeovers))
            movs = [m for m, in Changeover.query.with_entities(
                Changeover.movement_id).filter(Changeover.loc_string.in_(_changeovers)).all()]

            Changeover.query.filter(
                Changeover.loc_string.in_(_changeovers)).delete(synchronize_session=False)

            LION_SQLALCHEMY_DB.session.commit()

            objs_to_refresh = ShiftMovementEntry.query.filter(
                ShiftMovementEntry.movement_id.in_(movs)).all()

            if objs_to_refresh:

                for obj in objs_to_refresh:

                    obj.loc_string = ''
                    obj.tu = ''

                LION_SQLALCHEMY_DB.session.commit()

            Changeover.list_changeovers(clear=True)

        except SQLAlchemyError as e:
            LION_SQLALCHEMY_DB.session.rollback()
            return {'code': 400, 'message': f"Changeover deletion failed! {str(e)}"}

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            return {'code': 400, 'message': f"Changeover deletion failed! {log_exception(False)}"}

        return {'code': 200, 'message': f'{deleted_count} Changeover(s) deleted!'}

    def clear_user_changes(self):
        self._dct_user_changes = {}
        return {}

    def set_utilisation_slider_range(self, **dct_params):
        try:
            self._utilisation_range = dct_params['range']
            UI_PARAMS.update(utilisation_range=dct_params['range'])
            
            return {'status': ''}
        except Exception:
            self._utilisation_range = [0, 100]
            log_exception(
                popup=True, remarks='Setting utilisation range failed')

    def initialize_user_changes(self):

        self._dct_user_changes = {'dct_timechanges': {},
                                   'deletedmovements': set(),
                                   'newmovements': set(),
                                   'dct_shiftchanges': {}
                                   }

    def set_axis_ranges(self, **dct_params):
        UI_SHIFT_DATA.set_axis_ranges(**dct_params)

        UserParams.update(xAxis_range_start=UI_SHIFT_DATA.xAxis_range_start,
                            xAxis_range_end=UI_SHIFT_DATA.xAxis_range_end)

        return get_chart_data(page_num=dct_params['page_num'])

    def blank_shift(self, **dct_params):
        """
        Creates a blank shift with a minimum details in order to display in the drag and drop UI
        """

        try:

            __driver_loc = dct_params['start_loc']
            __page = dct_params['page_num']
            __driver = dct_params.get('driver_id', None)
            __operator = dct_params.get('operator', 'FedEx Express')
            __ctrl_by = dct_params['ctrl_by']
            __double_man = dct_params['double_man']
            __vhcle = int(dct_params['vehicle_type'])
            _shift_id = dct_params['shift_id']

            Operator.add_operator(operator_name=__operator)

            if __driver is None:
                idx = UI_SHIFT_DATA.dct_max_n_drivers_per_loc[__ctrl_by] + 1
                __str = ('0000000%d' % (idx))[-4:]
                __driver = '%s.%s' % (__ctrl_by, __str)
            else:
                if __driver.split('.')[0].strip() != __ctrl_by:
                    __driver = '%s.%s' % (__ctrl_by, __driver)

            __dct_blank_shift = {_shift_id: DctTour(**{
                'driver': __driver,
                'tour_id': 0,
                'list_loaded_movements': [],
                'tour_loc_from': __driver_loc,
                'tour_loc_string': '',
                'list_movements': [],
                'dep_date_time': UI_SHIFT_DATA.xAxis_range_noon_start,
                'arr_date_time': UI_SHIFT_DATA.xAxis_range_noon_end,
                'shift_end_datetime': UI_SHIFT_DATA.xAxis_range_noon_end,
                'driver_loc_mov_type_key': '',
                'is_fixed': False,
                'double_man': __double_man,
                'vehicle': __vhcle,
                'shift_id': _shift_id
            })}

            UI_SHIFT_DATA.update(
                dct_opt_drivers=__dct_blank_shift)

            UI_PARAMS.LIST_FILTERED_SHIFT_IDS.append(__driver)
            UI_PARAMS.DICT_DRIVERS_PER_PAGE[__page].append(__driver)

            return get_chart_data(page_num=__page)

        except Exception:
            self._display_err(
                f'Creating blank shift went wrong. {log_exception(False)}')

            return {}


    def _process_timechange(self, **dct_params):
        """
        Process time changes applied by the user via the drag and drop UI. If the impacted movements are part of a changeover,
        user will be notified that the time change is not allowed and a new changeover should be created.
        """

        __dct_user_changes = dct_params.get('dct_user_changes', {})

        __error_notifications = ''
        _timechane_notifications = ''
        _dct_time_changed_movements = {}

        try:

            dct_timechange = __dct_user_changes.get(
                'dct_timechanges', {})

            if dct_timechange:

                m_id = dct_timechange['movement_id']
                new_datetime = to_lion_datetime(dct_timechange['datetime'])

                changeover_string = UI_SHIFT_DATA.dict_all_movements[m_id].changeover_string

                if changeover_string != '':

                    movements = ShiftMovementEntry.changeover_movements(loc_string=changeover_string)

                    if len(movements) > 1:

                        msg = f"Time change not allowed! The movement is part of {changeover_string} changeover! "
                        msg = f"{msg}Please create a new changeover!"
                        return {'changeover_timechange_msg': msg, 'chart_data': get_chart_data()}

                    else:

                        obj = Changeover.query.with_entities(Changeover.tu_dest).filter(
                            Changeover.loc_string == changeover_string).first()

                        if obj:
                            try:

                                tu_dest = obj[0]

                                UI_SHIFT_DATA.dict_all_movements[movements[0]].update({'tu': tu_dest})
                                UI_SHIFT_DATA.dict_all_movements[movements[0]].update({'loc_string': ''})
                                Changeover.delete_changeovers(
                                    loc_string=changeover_string)

                            except Exception:
                                log_exception(popup=False,
                                               remarks=f"The chageover {changeover_string} clean up failed!")

                else:
                    movements = [m_id]

                total_seconds_chg = (
                    new_datetime - UI_SHIFT_DATA.dict_all_movements[m_id]['DepDateTime']).total_seconds()

                _lst_shift_loaded_movs = []
                _lst_shift_all_movs = []
                for mov in movements:

                    __dct_m = UI_SHIFT_DATA.dict_all_movements[mov]
                    self._dct_cached_movements[mov] = secure_copy(__dct_m)

                    _shift_id = __dct_m.shift_id

                    self._dct_cached_shifts[_shift_id] = secure_copy(
                        UI_SHIFT_DATA.optimal_drivers[_shift_id])

                    _lst_shift_loaded_movs = UI_SHIFT_DATA.optimal_drivers[_shift_id].list_loaded_movements
                    _lst_shift_all_movs = UI_SHIFT_DATA.optimal_drivers[_shift_id].list_movements

                    for _m in _lst_shift_loaded_movs:
                        if _m not in self._dct_cached_movements.keys():
                            self._dct_cached_movements.update({_m: secure_copy(
                                UI_SHIFT_DATA.dict_all_movements[_m])})

                    new_datetime = __dct_m['DepDateTime'] + \
                        timedelta(seconds=total_seconds_chg)

                    __dct_m.dep_date_time = new_datetime

                    if __dct_m.is_loaded():
                        _dct_time_changed_movements[mov] = __dct_m
                    
                    if _shift_id > 2:
                        UI_PARAMS.SET_IMPACTED_SHIFTS.update([_shift_id])
                    else:
                        UI_SHIFT_DATA.update(
                            dict_movements={mov: DictMovement(**__dct_m)}, 
                            dct_opt_drivers={_shift_id: UI_SHIFT_DATA.optimal_drivers[_shift_id]})

                for __shft in UI_PARAMS.SET_IMPACTED_SHIFTS:

                    if not _dct_time_changed_movements:
                        if are_movements_overlapped(list_of_movs=_lst_shift_all_movs):
                            return {'empty_movement_msg': "The time change results in overlapping movements in shift "
                                     f"{UI_SHIFT_DATA.optimal_drivers[__shft].driver}. Please adjust the time change!"}

                        continue

                    if SHIFT_MANAGER.refresh_shift_after_drag(
                            new_m=None,
                            dct_time_changed_movements=_dct_time_changed_movements,
                            shift_id=__shft):

                        UI_PARAMS.SET_IMPACTED_SHIFTS.update([__shft])

                        _timechane_notifications = f'{_timechane_notifications}{
                            SHIFT_MANAGER.notifications}'

                    else:
                        __error_notifications = f'{__error_notifications}{
                            SHIFT_MANAGER.exception_message}; '

        except Exception:
            __error_notifications = f"{__error_notifications}{log_exception(popup=False,
                                                                             remarks='Processing time changes failed!')}"

        if __error_notifications == '' and _timechane_notifications == '':
            return self.accept_user_changes(**dct_params)

        UI_PARAMS.SET_IMPACTED_SHIFTS = set()
        return {'notifications': _timechane_notifications}

    def process_user_changes(self, **dct_params):
        """
        This module manages changes applied by the user via the drag and drop UI. The changes such as

        - **Movement time changes:** This can be done by simply dragging a movement horizontally
        - **Movement shift changes:** This can be done by vertically dragging a movement between shifts on the UI
        - **Deleting a movement:** This can be done by dragging the movement to Recycle bin or ``2``
          or through right-click
        - **Deleting a shift:** This can be done by e.g., double clicking on a blank shift.

        __dct_user_changes = {
            'dct_timechanges': {'1000456': 'Mon 22:15', '1000459': 'Mon 20:19', '1001816': 'Mon 23:31'},
            'dct_shiftchanges': {'1000457': 'AE4.S11'},
            'deletedmovements': [['1123', 1000459], ['1124', 1000456], ['1125', 1001816]],
            'deletedshifts': ['1123']}

        # self._dct_user_changes = {'dct_timechanges': {},
        #                     'deletedmovements': set(),
        #                     'newmovements': set(),
        #                     'dct_shiftchanges': {}
        #                     }

        """

        self._dct_cached_shifts = {}
        self._dct_cached_movements = {}

        self._str_user_change_notifications = ''

        __dct_user_changes = dct_params['dct_user_changes']
        page_num = dct_params['page_num']

        UI_PARAMS.PAGE_NUM = page_num * 1
        UI_PARAMS.SET_IMPACTED_SHIFTS = set()

        __reverse_action_due_to_error = False
        __error_notifications = ''

        try:
            if __dct_user_changes.get('dct_timechanges', {}):
                return self._process_timechange(**dct_params)

        except Exception:
            log_exception(popup=False)
            return {}

        if not __dct_user_changes:
            return {}

        try:

            if not __dct_user_changes.get(
                    'dct_shiftchanges', {}):

                return get_chart_data(
                    **{'shift_data': UI_SHIFT_DATA})

            dct_shiftchanges = __dct_user_changes.get(
                'dct_shiftchanges', {})

            dct_shiftchanges = {int(m): v for m, v in dct_shiftchanges.items()}

            _set_shift_changes = set(dct_shiftchanges)
            movs_to_del = []

            for m in _set_shift_changes:

                if dct_shiftchanges[m] == 2:

                    chgover_str, _ = Changeover.get_movement_loc_string(
                        movment_id=m)

                    if chgover_str != '':

                        movs_to_del = ShiftMovementEntry.changeover_movements(
                            loc_string=chgover_str)

                        dct_shiftchanges.update({m1: 2 for m1 in movs_to_del})

                        Changeover.delete_changeovers(
                            loc_string=chgover_str)

            if movs_to_del:
                _set_shift_changes.update(movs_to_del)

            _set_all_movements = set(
                UI_SHIFT_DATA.dict_all_movements)

            for m in _set_shift_changes:

                shift_id = UI_SHIFT_DATA.dict_all_movements[m].shift_id

                if shift_id != 2:

                    for mid in UI_SHIFT_DATA.optimal_drivers[shift_id].list_movements:

                        if mid in _set_all_movements:
                            self._dct_cached_movements.update(
                                {mid: secure_copy(UI_SHIFT_DATA.dict_all_movements[mid])})

                    self._dct_cached_shifts[shift_id] = secure_copy(
                        UI_SHIFT_DATA.optimal_drivers[shift_id])

                shift_id2 = dct_shiftchanges[m]

                if shift_id2 not in [2]:

                    self._dct_cached_shifts[shift_id2] = secure_copy(
                        UI_SHIFT_DATA.optimal_drivers[shift_id2])

                    for mid in UI_SHIFT_DATA.optimal_drivers[shift_id2].list_movements:
                        if mid in _set_all_movements:
                            self._dct_cached_movements.update(
                                {mid: secure_copy(UI_SHIFT_DATA.dict_all_movements[mid])})

            # add all moved (shift changes or deleted) movements to the imacted movs
            # list to update the data in the db

            for m in _set_shift_changes:

                __shift = UI_SHIFT_DATA.dict_all_movements[m].shift_id

                if __shift == 1:
                    self._remove_movement_from_dump_area(m)
                    # SHIFT_MANAGER.shift_data = UI_SHIFT_DATA

                else:

                    if SHIFT_MANAGER.refresh_shift_after_drag(
                            removed_movements=[m],
                            shift_id=__shift):

                        UI_PARAMS.SET_IMPACTED_SHIFTS.update([__shift])

                    else:
                        __error_notifications = f'{__error_notifications}{
                            SHIFT_MANAGER.exception_message}; '

                        __reverse_action_due_to_error = True

                __shift2 = None
                if m in _set_shift_changes:

                    __shift2 = dct_shiftchanges[m]

                    if __shift2 == 1:
                        self.add_movement_to_dump_area(list_m=[m])

                    elif __shift2 == 2:
                        UI_SHIFT_DATA.delete_movement(m)

                    else:

                        if SHIFT_MANAGER.refresh_shift_after_drag(
                                new_m=m,
                                shift_id=__shift2):

                            UI_PARAMS.SET_IMPACTED_SHIFTS.update([__shift2])

                            self._str_user_change_notifications = '%s%s' % (
                                self._str_user_change_notifications, SHIFT_MANAGER.notifications)

                        else:
                            __error_notifications = '%s%s; ' % (
                                __error_notifications, SHIFT_MANAGER.exception_message)
                            __reverse_action_due_to_error = True

            if __reverse_action_due_to_error:

                __chart_data1 = get_chart_data(
                    **{'shift_data': UI_SHIFT_DATA})

                __nots = __chart_data1.get('notifications', '')
                if __nots != '':
                    __chart_data1['notifications'] = '%s. %s; ' % (
                        __nots, __error_notifications)
                else:
                    __chart_data1['notifications'] = __error_notifications

                if 'No feasible shift could be built.' in __error_notifications:
                    __chart_data1['popup'] = 'The change was cancelled: %s' % (
                        __error_notifications)
                elif 'movement cannot be assigned' in __error_notifications:
                    __chart_data1['popup'] = __error_notifications
                else:
                    __chart_data1['popup'] = 'The change was reversed due to system error. Please consult status.log file!'

                return __chart_data1

            if self._str_user_change_notifications == '':
                return self.accept_user_changes(**dct_params)
            else:
                __nots = '%s' % self._str_user_change_notifications
                self._str_user_change_notifications = ''
                return {'notifications': __nots}

        except Exception:

            log_exception(popup=False,
                           remarks='processing user changes failed!')

            __chart_data1 = get_chart_data(
                page_num=page_num,
                shift_data=UI_SHIFT_DATA
            )

            __chart_data1['all_changed_shifts'] = []

            return __chart_data1

    def accept_user_changes(self, **dct_params):
        """
        Accepts user changes and updates the shift data accordingly.

        Args:
            dct_params (dict): A dictionary containing the parameters for accepting user changes.
                - page_num (int): The page number.

        Returns:
            dict: A dictionary containing the updated chart data.

        Raises:
            ValueError: If refreshing the shift was not successful or saving the schedule failed.
        """

        try:
            page_num = dct_params.get('page_num', UI_PARAMS.PAGE_NUM)

            if UI_SHIFT_DATA is None:
                raise ValueError('Refreshing shift was not successful!')

            __page_drivers = UI_PARAMS.DICT_DRIVERS_PER_PAGE[page_num]
            __page_drivers.extend(
                [d for d in UI_PARAMS.SET_IMPACTED_SHIFTS if d not in __page_drivers])

            UI_PARAMS.LIST_FILTERED_SHIFT_IDS.extend(
                [d for d in UI_PARAMS.SET_IMPACTED_SHIFTS if d not in UI_PARAMS.LIST_FILTERED_SHIFT_IDS])

            UI_PARAMS.DICT_DRIVERS_PER_PAGE[page_num] = __page_drivers

            UI_SHIFT_DATA.store_modified_shifts(
                UI_PARAMS.SET_IMPACTED_SHIFTS)

            if not SaveSchedule().save_ok:
                raise ValueError('Saving schedule failed!')

            __chart_data1 = get_chart_data(
                page_num=page_num)

            __chart_data1['all_changed_shifts'] = []
            if 'notifications' in __chart_data1:
                del __chart_data1['notifications']

            return __chart_data1

        except Exception:
            log_exception(popup=True)

            __chart_data1 = get_chart_data(
                page_num=page_num)

            __chart_data1['all_changed_shifts'] = []

            return {}

    def reject_user_changes(self, **dct_params):

        try:

            _cached_shifts = set(self._dct_cached_shifts)
            _cached_movs = set(self._dct_cached_movements)

            _dict_movements = {}
            while _cached_movs:

                m = _cached_movs.pop()
                dct_m = self._dct_cached_movements.pop(m, {})

                if dct_m:
                    _dict_movements[m] = dct_m

                    if not ShiftMovementEntry.update_movement_info(dct_m=dct_m):
                        if not ShiftMovementEntry.add_dct_m(dct_m=dct_m):

                            raise ValueError(
                                'add_dct_m was not saved successfully in LocalMovements. ')

            _dct_opt_drivers = {}
            while _cached_shifts:

                sid = _cached_shifts.pop()
                dct_tour = self._dct_cached_shifts.pop(sid, {})
                if dct_tour:
                    _dct_opt_drivers[sid] = dct_tour

            DriversInfo.save_dct_tours(dct_tours=_dct_opt_drivers)

            UI_SHIFT_DATA.update(dct_opt_drivers=_dct_opt_drivers,
                                            dict_movements=_dict_movements)

            UI_PARAMS.SET_IMPACTED_SHIFTS = set()
            UI_PARAMS.SET_IMPACTED_SHIFTS = set()

        except Exception:
            log_exception(popup=False, remarks='reject_user_changes failed!')
            return {}

        return get_chart_data(**dct_params)

    def run_diagnostics(self):

        empty_dir(LION_DIAGNOSTICS_PATH)

        try:
            UI_SHIFT_DATA.run_diagnostics()
            __files = listdir(LION_DIAGNOSTICS_PATH)

            if not __files:
                return {'code': 200, 'message': 'No issue was found!'}

            return {'code': 200, 
                    'message':  f'Running diagnostics finished successfully: {len(__files)} issue files.'}

        except Exception:
            return {'code': 400, 'message': 'Running diagnostics failed!'}
        
    
    # Modify or change movement details

    def modify_movement_details(self, **dct_params):
        """
        Modifies the movement details based on the provided parameters. This module is called when user
        right/double clicks on a movement to modify its details such as loc_string, TU, TrafficType, etc. Based on
        the changes, the shift data is updated and saved.

        Args:
            dct_params (dict): A dictionary containing the parameters for modifying the movement details.

        Returns:
            dict: A dictionary containing the updated chart data.

        Raises:
            ValueError: If the MovementID could not be detected or if saving the movement data failed.
            Exception: If an error occurs while updating the movement details.

        """

        __error_notifications = ''

        self._dct_cached_movements = {}
        self._dct_cached_shifts = {}
        UI_PARAMS.SET_IMPACTED_SHIFTS = set()

        try:

            __loc_string = dct_params.get('loc_string', '')
            __locstrng2list = __loc_string.split(LOC_STRING_SEPERATOR)

            if len(__locstrng2list) > 3:
                __msg = 'The movement seems to be part of a C/O; or you entered an invalid loc string.'
                __msg = '%s%s' % (
                    __msg, 'To change time only, you can drag a leg of C/O.')

                self._display_info(__msg)
                return {}

            __mid = int(dct_params.get('movementid', 0))

            if not __mid:
                raise ValueError(
                    'MovementID could not be detected. Please try again!')

            # Note that __dct_m is of type DictMovement
            __dct_m: DictMovement = UI_SHIFT_DATA.dict_all_movements[__mid]

            page_num = dct_params.get('page_num', 1)
            __traffic_type = dct_params.get('traffic_type', '')
            _tu_dest = dct_params.get('tu_dest', '')
            __depday = dct_params.get('depday', 'Mon')
            __shiftname = __dct_m['shift']
            shift_id = __dct_m['shift_id']

            for mid in UI_SHIFT_DATA.optimal_drivers[shift_id].list_movements:
                self._dct_cached_movements.update(
                    {mid: secure_copy(UI_SHIFT_DATA.dict_all_movements[mid])})

            self._dct_cached_shifts.update(
                {shift_id: secure_copy(UI_SHIFT_DATA.optimal_drivers[shift_id])})

            __rebuild_m = False

            if __dct_m['tu'] != _tu_dest:
                __dct_m.update({'tu': _tu_dest})

            if __dct_m['TrafficType'] != __traffic_type and __traffic_type != '':
                __dct_m.update({'TrafficType': __traffic_type})

            if __loc_string != \
                    UI_SHIFT_DATA.dict_all_movements[__mid].loc_string:

                __rebuild_m = True

            if __rebuild_m:

                if len(__locstrng2list) > 3:

                    __msg = 'Invalid loc string OR the movement is a leg of a C/O; '
                    __msg = '%s%s' % (
                        __msg, 'For time change only, you can drag a leg of C/O.')

                    self._display_info(__msg)
                    return {}

                __dep_dt = combine_date_time(
                    LION_DATES[__depday], __locstrng2list[2])

                __dct_m = UI_MOVEMENTS.rebuild_movement(m=__mid,
                                                            orig=__locstrng2list[0],
                                                            dest=__locstrng2list[1],
                                                            traffic_type=__dct_m['TrafficType'],
                                                            tu_loc=__dct_m['tu'],
                                                            loc_string=__loc_string,
                                                            DepDateTime=__dep_dt,
                                                            ArrDateTime=None,
                                                            vehicle=__dct_m['VehicleType'],
                                                            shift=__shiftname,
                                                            shift_id=shift_id)

                UI_SHIFT_DATA.update(
                    dict_movements={__mid: __dct_m})

                __rebuild_m = __rebuild_m and (
                    shift_id != 1)

            if __rebuild_m:

                # SHIFT_MANAGER.shift_data = UI_SHIFT_DATA
                # __active_shift_data_backup = copy_obj(UI_SHIFT_DATA)

                if SHIFT_MANAGER.refresh_shift_after_drag(
                        shift_id=shift_id):

                    UI_PARAMS.SET_IMPACTED_SHIFTS.update([shift_id])

                    __chart_data1 = get_chart_data(
                        **{'page_num': page_num})

                    __chart_data1['all_changed_shifts'] = []
                    __chart_data1['notifications'] = ''

                    __notifications = SHIFT_MANAGER.notifications

                    UI_SHIFT_DATA.store_modified_shifts(
                        UI_PARAMS.SET_IMPACTED_SHIFTS)

                    if __notifications != '':
                        self._display_info(__notifications)

                    if not SaveSchedule().save_ok:
                        raise Exception('Failed to save schedule changes!')

                    return __chart_data1

                else:

                    self.undo()
                    __error_notifications = SHIFT_MANAGER.exception_message

                    __chart_data1 = get_chart_data(
                        **{'page_num': page_num,
                           'shift_data': UI_SHIFT_DATA
                           })

                    __nots = __chart_data1['notifications']
                    if __nots != '':
                        __chart_data1['notifications'] = '%s. %s' % (
                            __nots, __error_notifications)
                    else:
                        __chart_data1['notifications'] = __error_notifications

                    if 'No feasible shift could be built.' in __error_notifications:
                        __chart_data1['popup'] = 'The change was cancelled: %s' % (
                            __error_notifications)

                    else:
                        __chart_data1['popup'] = 'The change was reversed due to system error. Please consult status.log file!'

                    self._display_info(__error_notifications)
                    return __chart_data1

            else:

                __loc_string = UI_SHIFT_DATA.dict_all_movements[__mid].loc_string

                UI_SHIFT_DATA.dict_all_movements[__mid].update(
                    {'TrafficType': __dct_m['TrafficType']})

                UI_SHIFT_DATA.dict_all_movements[__mid].update(
                    {'tu': __dct_m['tu']})

                _shift_id = UI_SHIFT_DATA.dict_all_movements[__mid].get(
                    'shift_id', 0)

                if not _shift_id:
                    raise ValueError(
                        'Cannot modify traffic type as shift name is unknown!')

                if not SaveSchedule(impacted_movements=[__mid]).save_ok:
                    raise ValueError('Saving movement data failed!')

        except Exception:
            log_exception(
                popup=True, remarks='Updating modify_movement_details failed.')

            return {}

        return get_chart_data(**{'page_num': page_num})

    def barwith_enlarge(self, **dct_params):
        self._bar_width = [int(x * 1.10) for x in self._bar_width]
        UserParams.update(bar_width=';'.join(
            [str(x) for x in self._bar_width]))
        
        UI_PARAMS.update(bar_width=self._bar_width)
        return get_chart_data(**dct_params)

    def barwith_shrink(self, **dct_params):
        self._bar_width = [int(x * 0.9) for x in self._bar_width]
        UserParams.update(bar_width=';'.join(
            [str(x) for x in self._bar_width]))
        
        UI_PARAMS.update(bar_width=self._bar_width)
        return get_chart_data(**dct_params)


    def is_basket_empty(self):
        try:
            _existing_shifts = basket_shifts.get_basket_shift_ids()
            return len(_existing_shifts) == 0
        except Exception:
            log_exception(popup=False)

            return True

    def add_shifts_to_my_basket(self, **dct_params):

        try:
            __drivers = dct_params['drivers']
            __get_right_click_id = dct_params['get_right_click_id']

            if not __drivers:
                if __get_right_click_id:
                    __drivers = [UI_PARAMS.RIGHT_CLICK_ID]

            if __drivers:

                _str_existing_shifts = str(UserParams.get_param(
                    param='basket_shifts', if_null=''))

                self.my_shifts_in_basket = []
                if _str_existing_shifts != '':

                    self.my_shifts_in_basket = _str_existing_shifts.split(
                        '|')
                    self.my_shifts_in_basket = [
                        int(x) for x in self.my_shifts_in_basket if str(x).isnumeric()]

                if self.my_shifts_in_basket:
                    __drivers = [
                        d for d in __drivers if d not in self.my_shifts_in_basket]

                self.my_shifts_in_basket.extend(__drivers)

                self.my_shifts_in_basket = list(
                    set(self.my_shifts_in_basket))

                if self.my_shifts_in_basket:
                    UserParams.update(basket_shifts='|'.join(
                        str(x) for x in self.my_shifts_in_basket))

                self.my_shifts_in_basket = [
                    int(x) for x in self.my_shifts_in_basket]
                UI_PARAMS.OPTIONS.update(
                    {'basket_drivers': self.my_shifts_in_basket})

        except Exception:

            pre_load_my_shifts_in_basket()
            log_exception(
                popup=False, remarks='Adding shift to my basket failed.')

        return {'drivers': self.my_shifts_in_basket}

    def remove_shifts_from_my_basket(self, **dct_params):

        __drivers = dct_params['drivers']
        __get_right_click_id = dct_params['get_right_click_id']

        if not __drivers:
            if __get_right_click_id:
                __drivers.append(UI_PARAMS.RIGHT_CLICK_ID)

        if __drivers:

            self.my_shifts_in_basket = []

            try:

                _str_existing_shifts = UserParams.get_param(
                    param='basket_shifts', if_null='')

                if _str_existing_shifts != '':

                    self.my_shifts_in_basket = _str_existing_shifts.split(
                        '|')

                    self.my_shifts_in_basket = [
                        int(x) for x in self.my_shifts_in_basket if len(str(x)) > 2]

                    self.my_shifts_in_basket = [
                        d for d in self.my_shifts_in_basket if d not in __drivers]

                    self.my_shifts_in_basket = list(
                        set(self.my_shifts_in_basket))

                    if self.my_shifts_in_basket:
                        UserParams.update(basket_shifts='|'.join(
                            [str(x) for x in self.my_shifts_in_basket]))

                    self.my_shifts_in_basket = [
                        int(x) for x in self.my_shifts_in_basket]
                    UI_PARAMS.OPTIONS.update(
                        {'basket_drivers': self.my_shifts_in_basket})

            except Exception:
                pre_load_my_shifts_in_basket()
                log_exception(
                    popup=False, remarks='Removing shift(s) from my basket failed.')

        return {'drivers': self.my_shifts_in_basket}

    def load_m_into_dump_area(self, **dct_params):

        try:

            __movementid = int(dct_params['movementid'])
            page_num = dct_params['page_num']

            self.add_movement_to_dump_area(
                list_m=[__movementid])

        except Exception:
            log_exception(
                popup=False, remarks='load_mov_into_dump_area failed!')

        return get_chart_data(page_num=page_num)

    def draw_tour(self, **dct_params):

        try:

            shift = int(dct_params.get('shift_id', 0))
            if not shift:
                shift = UI_PARAMS.RIGHT_CLICK_ID

            tour = UI_SHIFT_DATA.optimal_drivers[shift]

            locs = tour['tour_loc_string'].split('->')
            movements = tour['list_movements']

            dct_utilisation = {str(x): (0.01 if self._is_loaded.is_loaded(x) else 0)
                               for x in movements}

            dct_tour = {'locs': locs,
                        'movements': movements,
                        'dict_utilisation': dct_utilisation,
                        'polyline': self._arrow.get_arrow_points(
                            loc_codes=locs,
                            movements=movements)
                        }

            for loc in locs:
                dct_tour.update({loc: {'latitude': Location.to_dict()[loc]['latitude'],
                                       'longitude': Location.to_dict()[loc]['longitude'],
                                       'town': Location.to_dict()[loc]['town']}})

            return {UI_PARAMS.RIGHT_CLICK_ID: dct_tour}

        except Exception:

            log_exception(
                popup=True, remarks=f'The shift cannot be displayed for {UI_PARAMS.RIGHT_CLICK_ID}!')

        return {}

    def load_available_scenarios(self, **dct_params):

        try:
            lst_scnarios_db = Scenarios.get_available_scenarios()
            return {'scenarios': lst_scnarios_db}

        except Exception:
            log_exception(
                popup=False, remarks=f'load_available_scenarios failed!')

        return {'scenarios': []}

    def refresh_tour_string(self):

        try:
            list_changeovers = Changeover.list_changeovers()
        except Exception:
            list_changeovers = []
            log_exception(
                popup=False, remarks=f'list_changeovers failed!')

        if not UI_SHIFT_DATA.optimal_drivers:

            return {'dct_shift_string': {},
                    'dct_loc_string': {},
                    'dct_unplanned_movements': {},
                    'dct_co': {},
                    'selected_shifts': [],
                    'selected_co': [],
                    'selected_weekdays': self._filtering_wkdays,
                    'list_changeovers': list_changeovers,
                    'selected_vehicles': [str(x) for x in self._selected_vehicles]}

        try:
            __dct_unplanned_movements = self.refresh_unplanned_movs()
            __dct_loc_string = UI_SHIFT_DATA.dct_loc_string

        except Exception:
            __dct_loc_string = {}
            __dct_unplanned_movements = {}

        try:
            if len(UI_PARAMS.LIST_FILTERED_SHIFT_IDS) < len(UI_SHIFT_DATA.optimal_drivers) - 2:
                return {
                    'dct_loc_string': __dct_loc_string,
                    'selected_weekdays': self._filtering_wkdays,
                    'list_changeovers': list_changeovers,
                    'selected_co': list(self._set_selected_changeovers),
                    'selected_shifts': UI_PARAMS.LIST_FILTERED_SHIFT_IDS,
                    'dct_unplanned_movements': __dct_unplanned_movements,
                    'selected_vehicles': [str(x) for x in self._selected_vehicles]}

            return {
                'dct_loc_string': __dct_loc_string,
                'selected_weekdays': self._filtering_wkdays,
                'list_changeovers': list_changeovers,
                'selected_shifts': [],
                'dct_unplanned_movements': __dct_unplanned_movements,
                'selected_co': [],
                'selected_vehicles': [str(x) for x in self._selected_vehicles]}

        except Exception:
            log_exception(
                popup=False, remarks=f'refresh_tour_string failed!')

            return {}

    def undo(self):
        # return self.reject_user_changes()
        try:

            _cached_shifts = set(self._dct_cached_shifts)
            _cached_movs = set(self._dct_cached_movements)

            _dict_movements = {}
            while _cached_movs:

                m = _cached_movs.pop()
                dct_m = self._dct_cached_movements.pop(m, {})
                if dct_m:
                    _dict_movements[m] = dct_m

            _dct_opt_drivers = {}
            while _cached_shifts:

                sid = _cached_shifts.pop()
                dct_tour = self._dct_cached_shifts[sid]
                if dct_tour:
                    _dct_opt_drivers[sid] = dct_tour

            UI_SHIFT_DATA.update(dct_opt_drivers=_dct_opt_drivers,
                                            dict_movements=_dict_movements)

            if not SaveSchedule(impacted_shifts=list(self._dct_cached_shifts)).save_ok:

                raise ValueError('SaveSchedule was not successful. ')

        except Exception:
            self._dct_cached_shifts = {}
            self._dct_cached_movements = {}
            log_exception(popup=True, remarks='Undo operation failed!')
            return {}

        self._dct_cached_shifts = {}
        self._dct_cached_movements = {}

        return get_chart_data()

    def toggle_fixing_shifts(self, **dct_params):

        try:
            _shiftid = int(dct_params.get('shift_id', 0))
            if not _shiftid:
                _shiftid = UI_PARAMS.RIGHT_CLICK_ID
            
            _dct_drivers_to_save = {}

            if _shiftid in UI_SHIFT_DATA.optimal_drivers:

                __is_fx = UI_SHIFT_DATA.optimal_drivers[_shiftid]['is_fixed']
                [UI_SHIFT_DATA.optimal_drivers[_shiftid].update({'is_fixed': not __is_fx})]

                _dct_drivers_to_save.update(
                    {_shiftid: UI_SHIFT_DATA.optimal_drivers[_shiftid]})

        except Exception:
            log_exception(popup=True, remarks='operation failed!')
            return {}

        if _dct_drivers_to_save:
            try:
                DriversInfo.save_dct_tours(dct_tours=_dct_drivers_to_save)
            except Exception:
                log_exception(
                    popup=False, remarks='The changes could not be saved!')

        try:
            return get_chart_data()
        except Exception:
            log_exception(
                popup=True, remarks='toggle_fixing_shifts failed!')
            
            return {}
        
    def delete_if_blank_else_fixUnfix(self, **dct_params):

        try:
            _shiftid = int(dct_params['shift'])
            __pg_num = dct_params['page_num']
            _dct_drivers_to_save = {}

            if not UI_SHIFT_DATA.optimal_drivers.get(
                    _shiftid, {}).get('list_loaded_movements', []):

                UI_SHIFT_DATA.remove_shift(shift_id=_shiftid)
            else:
                __is_fx = UI_SHIFT_DATA.optimal_drivers[_shiftid]['is_fixed']
                [UI_SHIFT_DATA.optimal_drivers[_shiftid].update(
                    {'is_fixed': not __is_fx})]

                _dct_drivers_to_save.update(
                    {_shiftid: UI_SHIFT_DATA.optimal_drivers[_shiftid]})

        except Exception:
            log_exception(popup=True, remarks='operation failed!')
            return {}

        if _dct_drivers_to_save:
            try:
                DriversInfo.save_dct_tours(
                    dct_tours=_dct_drivers_to_save)

            except Exception:
                log_exception(
                    popup=False, remarks='The changes could not be saved!')

        try:
            return get_chart_data(page_num=__pg_num)

        except Exception:
            log_exception(
                popup=True, remarks='delete_if_blank_else_fixUnfix failed!')
            return {}

    def update_fixed_tours(self, **dct_params):

        try:
            user_provided_shift_ids = dct_params.get('drivers', set())
            unfix_all_flag = dct_params.get('unfix_all', 'No') == 'Yes'
            fix_all_flag = dct_params.get('fix_all', 'No') == 'Yes'
            page_num = dct_params['page_num']

            sids_to_save = set()

            if unfix_all_flag:

                __set_drvers = set([d for d in UI_PARAMS.LIST_FILTERED_SHIFT_IDS
                                    if d in UI_SHIFT_DATA.optimal_drivers.keys()])

                user_provided_shift_ids = set([d for d in __set_drvers
                                                if UI_SHIFT_DATA.optimal_drivers[d]['is_fixed']])

                sids_to_save.update(user_provided_shift_ids)

                [UI_SHIFT_DATA.optimal_drivers[__driver].update(
                    {'is_fixed': False}) for __driver in user_provided_shift_ids]

            elif fix_all_flag:

                __set_drvers = set([d for d in UI_PARAMS.LIST_FILTERED_SHIFT_IDS
                                    if d in UI_SHIFT_DATA.optimal_drivers.keys()])

                user_provided_shift_ids = set([
                    d for d in __set_drvers if not UI_SHIFT_DATA.optimal_drivers[d]['is_fixed']])

                [UI_SHIFT_DATA.optimal_drivers[__driver].update({'is_fixed': True}) 
                 for __driver in user_provided_shift_ids]
                
                sids_to_save.update(user_provided_shift_ids)

            elif user_provided_shift_ids:

                __set_drvers = set([d for d in UI_PARAMS.LIST_FILTERED_SHIFT_IDS
                                    if d in user_provided_shift_ids and d in UI_SHIFT_DATA.optimal_drivers.keys()])

                for __driver in __set_drvers:

                    __is_fx = UI_SHIFT_DATA.optimal_drivers[__driver]['is_fixed']
                    [UI_SHIFT_DATA.optimal_drivers[__driver].update({'is_fixed': not __is_fx})]

                sids_to_save.update(__set_drvers)

            else:
                raise ValueError('No driver has been selected!')

        except Exception:
            return {'update_fixed_tours_message': log_exception(popup=False, remarks='update_fixed_tours failed!'),
                    'chart_data': {}}

        _dct_drivers = {}
        for sid in sids_to_save:

            dct_tour = UI_SHIFT_DATA.optimal_drivers.get(sid, {})
            if dct_tour:
                _dct_drivers[sid] = secure_copy(dct_tour)

        if _dct_drivers:
            DriversInfo.save_dct_tours(dct_tours=_dct_drivers)

        return {'update_fixed_tours_message': f"Successfully updated {len(user_provided_shift_ids)} tours!", 
                'chart_data': get_chart_data(page_num=page_num)}

    def toggle_search_current_page(self, **dct_params):

        try:
            self.search_current_page_only_flag = dct_params['search_curr_page']
        except Exception:
            log_exception(
                popup=False, remarks='toggle_search_current_page failed!')
            self.search_current_page_only_flag = False

    def un_hide_infeas(self, **dct_params):

        try:
            UI_PARAMS.HIDE_INFEASIBLE = dct_params.get('hide', False)
            status = apply_filters()

            if status.get('code', 200) != 400:
                return get_chart_data()

            raise Exception(status['error'])

        except Exception:
            
            return {}

    def un_hide_fixed(self, **dct_params):

        UI_PARAMS.HIDE_FIXED = dct_params['hide']
        return get_chart_data(page_num=dct_params['page_num'])

    def un_hide_blank(self, **dct_params):

        UI_PARAMS.HIDE_BLANK = dct_params['hide']
        return get_chart_data(page_num=dct_params['page_num'])

    def preview_driver_report(self, drivers=[], full_weekPlan=False):

        __status_msg_dep_arr = ''

        try:

            DRIVER_REPORT.initialize()

            if full_weekPlan:

                self._dep_arr_report_obj = DepArrReport(preview_only=True)
                self._dep_arr_report_obj.configure_base_data()
                self._dep_arr_report_obj.dump_directory = LION_LOCAL_DRIVER_REPORT_PATH

            DRIVER_REPORT.dump_directory = LION_LOCAL_DRIVER_REPORT_PATH

            if not full_weekPlan:

                if not drivers:
                    drivers = UI_PARAMS.DICT_DRIVERS_PER_PAGE[UI_PARAMS.PAGE_NUM]

                if not drivers:
                    self._display_info(
                        'PLease select a shift to preview its report!')

                    return DataFrame()

                DRIVER_REPORT.gen_report_base(shift_ids=drivers)

            else:
                DRIVER_REPORT.gen_report_base()

            _df_driver_plan_week = DataFrame()

            for wkday in WEEKDAYS_NO_SAT:

                try:

                    if full_weekPlan:

                        __status = self._dep_arr_report_obj.gen_dep_arr_report(
                            wkday=wkday)

                        if __status != '':
                            __status_msg_dep_arr = '%s. %s' % (
                                __status_msg_dep_arr, __status)

                        drivers = list(
                            self._dep_arr_report_obj.dct_optimal_drivers)

                    _df_driver_plan = DRIVER_REPORT.gen_report(
                        drivers=drivers, return_driver_report=True, wkday=wkday)

                except Exception:
                    _df_driver_plan = DataFrame()
                    log_exception(
                        popup=False, remarks=f'preview_driver_report for selected drivers failed on {wkday}!')

                if not _df_driver_plan.empty:
                    _df_driver_plan_week = concat(
                        [_df_driver_plan_week, _df_driver_plan])

            _df_driver_plan_week['wkdayidx'] = _df_driver_plan_week.weekday.apply(
                lambda x: WEEKDAYS_NO_SAT.index(x))

            _df_driver_plan_week.sort_values(
                by=['driver', 'wkdayidx'], inplace=True)

            _df_driver_plan_week.drop(['wkdayidx'], axis=1, inplace=True)

        except Exception:
            _df_driver_plan_week = DataFrame()
            log_exception(
                popup=True, remarks=f'preview_driver_report for selected drivers failed!')

        if 'failed' in __status_msg_dep_arr != '':
            self._display_err(__status_msg_dep_arr)

        return _df_driver_plan_week

    def gen_driver_report(self, **dct_params):
        """
        This module generate three main categories of driver reports.
        * If __drivers is provided, driver plan for the specified drivers will be generated but not published
        * If page_num is provided, driver plan for drivers in the specified page will be generated but not published
        * If __dayreport is selected, driver plan for the specified day will be generated but not published
        """

        DRIVER_REPORT.initialize()
        DRIVER_REPORT.right_click_id = False

        if dct_params.get('get_right_click_id', False):
            __drivers = [UI_PARAMS.RIGHT_CLICK_ID]
            DRIVER_REPORT.right_click_id = True
        else:
            __drivers = dct_params.get('drivers', [])

        page_num = dct_params.get('page_num', None)
        _weekdays = dct_params.get('weekdays', [])
        _publish = dct_params.get('publish', False)
        _no_pdf = dct_params.get('no_pdf', False)

        __status_msg = ''

        DRIVER_REPORT.page_export = page_num is not None

        __days = []
        _t0 = datetime.now()

        _dump_dir = f'{LION_DRIVER_REPORT_DIST_PATH}' if _publish else f'{
            LION_LOCAL_DRIVER_REPORT_PATH}'

        _csv_reports_dir = ''
        if not _publish:
            _csv_reports_dir = _dump_dir
            empty_dir(path_to_empty=LION_LOCAL_DRIVER_REPORT_PATH)

        DRIVER_REPORT.dump_directory = _dump_dir

        if not page_num:
            self._dep_arr_report_obj = DepArrReport()
            self._dep_arr_report_obj.configure_base_data()
            self._dep_arr_report_obj.dump_directory = _dump_dir

        try:

            __days.extend(WEEKDAYS_NO_SAT)

            if _weekdays:
                __days = [d for d in __days if d in _weekdays]

            if not page_num:

                DRIVER_REPORT.gen_report_base()

                for __wkday in __days:

                    objStatus = DRIVER_REPORT.gen_report(
                        wkday=__wkday, no_pdf=_no_pdf)

                    if objStatus.status_msg != '':
                        __status_msg = '%s. %s' % (
                            __status_msg, objStatus.status_msg)

                    if not _no_pdf:
                        __status = self._dep_arr_report_obj.gen_dep_arr_report(
                            wkday=__wkday)

                        if __status != '':
                            __status_msg = '%s. %s' % (
                                __status_msg, __status)

                self.consolidate_driver_reports(
                    pr_cons_driver_rep_path=_csv_reports_dir)

            else:

                __status_msg = ''
                if not __drivers:
                    __drivers = set([d for d in
                                    UI_PARAMS.DICT_DRIVERS_PER_PAGE[page_num] if d not in [
                                        2, 1]])

                DRIVER_REPORT.gen_report_base(shift_ids=__drivers)
                for dy in WEEKDAYS_NO_SAT:

                    objStatus = DRIVER_REPORT.gen_report(
                        drivers=list(__drivers),
                        wkday=dy,
                        no_pdf=_no_pdf)

                    if objStatus.status_msg != '':
                        __status_msg = '%s. %s' % (
                            __status_msg, objStatus.status_msg)

        except Exception:
            log_exception(
                popup=True, remarks='Generating driver report failed!')

            return

        __t1 = datetime.now()
        if __status_msg == '':
            __status_msg = f'Driver plan has successfully exported in {_dump_dir}.\n' + \
                'Runtime: %s' % (
                    str(timedelta(seconds=int((__t1 - _t0).total_seconds()))))
        else:
            __status_msg = '%s.\nRuntime: %s' % (__status_msg, str(
                timedelta(seconds=int((__t1 - _t0).total_seconds()))))

        DRIVER_REPORT.to_blob_storage()
        self._display_info(__status_msg)

    def consolidate_driver_reports(self, pr_cons_driver_rep_path=''):

        __df_driver_report = DataFrame()

        try:

            if pr_cons_driver_rep_path == '':
                pr_cons_driver_rep_path = f'{LION_CONSOLIDATED_REPORT_PATH}'

            __OK_csvfiles = ['df_driver_report_Mon.csv', 'df_driver_report_Tue.csv', 'df_driver_report_Wed.csv',
                             'df_driver_report_Thu.csv', 'df_driver_report_Fri.csv', 'df_driver_report_Sat.csv',
                             'df_driver_report_Sun.csv']

            __csvfiles = [f for f in listdir(
                pr_cons_driver_rep_path) if f in __OK_csvfiles]

            for __csvfile in __csvfiles:

                try:
                    df = read_csv(
                        os_path.join(pr_cons_driver_rep_path, __csvfile), low_memory=False)
                except Exception:
                    df = DataFrame()
                    log_exception(
                        popup=False, remarks=f"Reading {__csvfile} failed! ")

                if not df.empty:
                    __df_driver_report = concat(
                        [__df_driver_report, df])

            export_dataframe_as_csv(dataframe=__df_driver_report.copy(), csv_file_path=os_path.join(
                pr_cons_driver_rep_path, 'df_driver_report.csv'))

            for clnm in ['remarks', 'notes', 'dep_day', 'DepDateTime', 'ArrDateTime']:
                if clnm in __df_driver_report.columns.tolist():
                    __df_driver_report.drop(
                        columns=[clnm], axis=1, inplace=True)

            __df_driver_report.rename(columns=(
                {'strDepDateTime': 'Start Time',  'strArrDateTime': 'End Time'}), inplace=True)

        except Exception:
            log_exception(popup=True,
                           remarks='Generated consolidated driver report failed!')
            __df_driver_report = DataFrame()

        if not __df_driver_report.empty:

            try:
                __stn_wb_path = os_path.join(
                    pr_cons_driver_rep_path, 'consolidated_driver_plan.xlsx')

                if 'From' in __df_driver_report.columns:

                    __df_driver_report['From'] = __df_driver_report.From.apply(
                        lambda x: f"{x}/{Location.to_dict().get(x, {}).get('location_name', '')}")

                    __df_driver_report['To'] = __df_driver_report.To.apply(
                        lambda x: f"{x}/{Location.to_dict().get(x, {}).get('location_name', '')}")

                    __df_driver_report['TU Destination'] = __df_driver_report['TU Destination'].apply(
                        lambda x: '' if x == '' else f"{x}/{Location.to_dict().get(x, {}).get('location_name', '')}")

                    __df_driver_report.rename(
                        columns={'From': 'Start Point', 'To': 'End Point'}, inplace=True)

                __cols = ['weekday', 'Driver', 'Start Point', 'End Point', 'TU Destination', 'Start Time', 'End Time',
                          'Driving Time', 'Distance (miles)', 'Traffic Type', 'vehicle', 'operator']

                xlwriter(df=__df_driver_report.loc[:, __cols].copy(), sheetname='DriverPlan',
                         xlpath=__stn_wb_path, echo=False)

            except Exception:
                log_exception(popup=True,
                               remarks='Could not generate consolidated_driver_plan.xlsx!')

    def load_location_info(self, **dct_params):
        try:

            __new_loc_code_to_edit = dct_params['Loc_to_edit']
            _dct = Location.to_dict().get(__new_loc_code_to_edit, {})

            live_stand_load = _dct.get('live_stand_load', 'stand').lower()
            _dct.update(
                {'live_stand_load': 'stand' if 'stand' in live_stand_load else 'live'})

            if _dct:
                return _dct

            self._display_err(
                f'No data was found for {__new_loc_code_to_edit}!')

        except Exception:
            self._display_err(log_exception(
                popup=False, remarks='load_location_info failed!'))

            return {}

    def handle_location(self, **dct_params):

        try:
            __new_loc_code_to_edit = dct_params['Loc_to_edit']

            if __new_loc_code_to_edit != '':
                __new_loc_code = __new_loc_code_to_edit
            else:
                __new_loc_code = dct_params['new_loc_code']

            __new_loc_code = __new_loc_code.upper()
            __close_loc = dct_params['close_loc']

            if __close_loc:
                __dct_info = Location.to_dict().get(
                    __new_loc_code, {})

                if __dct_info:
                    __dct_info.update(
                        {'active': not __dct_info.get('active', True)})

                    Location.update(**__dct_info)

                return

            __dct_new_loc_info = defaultdict(dict)
            __new_loc_name = dct_params['new_loc_name']
            __new_loc_type = dct_params['new_loc_type']
            __new_loc_coords = dct_params['new_loc_coords']
            __new_loc_town = dct_params['new_loc_town']
            __new_loc_turnaround = dct_params['new_loc_turnaround']
            __zipcode = dct_params['zipcode']
            __new_loc_debrief = dct_params['new_loc_debrief']
            __close_loc = dct_params['close_loc']
            # For customers a ctrl depo must be specified
            __ctrl_depot = dct_params['ctrl_depot']
            __live_stand_load = dct_params['live_stand_load']

            __live_stand_load = 'Stand Load' if __live_stand_load in [
                'stand', ''] else 'Live Load'

            if __new_loc_coords == '':
                raise ValueError('Coordinates cannot be NoneType.')

            latitude, longitude = [float(str(x).strip())
                                   for x in __new_loc_coords.split(',')]

            if latitude * longitude == 0:
                raise ValueError('Coordinates cannot be NoneType.')

            __dct_new_loc_info[__new_loc_code].update({
                'active': 1,
                'arr_debrief_time': int(str(__new_loc_debrief).split(',')[1].strip()),
                'chgover_driving_min': int(str(__new_loc_turnaround).split(',')[0].strip()),
                'chgover_non_driving_min': int(str(__new_loc_turnaround).split(',')[1].strip()),
                'country_code': UI_PARAMS.LION_REGION,
                'dep_debrief_time': int(str(__new_loc_debrief).split(',')[0].strip()),
                'latitude': latitude,
                'loc_code': __new_loc_code,
                'loc_type': __new_loc_type,
                'location_name': __new_loc_name,
                'ctrl_depot': __ctrl_depot,
                'longitude': longitude,
                'remarks': 'No remarks',
                'town': __new_loc_town,
                'postcode': __zipcode,
                'turnaround_min': sum([int(str(x).strip()) for x in __new_loc_turnaround.split(',')]),
                'utcdiff': 0,
                'update_on': datetime.now().strftime('%Y%m%d'),
                'live_stand_load': __live_stand_load})

            if not Location.update(**dict(__dct_new_loc_info[__new_loc_code])):
                raise Exception(f"The location {__new_loc_code} was not added!")
            
            refresh_options(dict_footprint=Location.to_dict())
            UI_TOUR_ANALYSIS.reset()

            self._display_info(
                f'Location data updated successfully for {__new_loc_code}!')

        except Exception:
            log_exception(popup=True, remarks='handle_location info failed!')
            return

    def remove_shift(self, **dct_params):
        """
        Deleting a shift
        """
        driver_id = dct_params.get('driver_id', None)

        if not driver_id:
            driver_id = UI_PARAMS.RIGHT_CLICK_ID
            UI_PARAMS.RIGHT_CLICK_ID = 0

        if not str(driver_id).isnumeric():
            driver_id = DriversInfo.get_shift_id(shiftname=driver_id)

        if not driver_id:
            return {'message': 'No shift has been selected!'}

        status = 'NOK'
        if driver_id in UI_SHIFT_DATA.optimal_drivers:
            status = UI_SHIFT_DATA.remove_shift(shift_id=driver_id)

        if status == 'OK':

            page_shifts = UI_PARAMS.DICT_DRIVERS_PER_PAGE[UI_PARAMS.PAGE_NUM]
            UI_PARAMS.DICT_DRIVERS_PER_PAGE[UI_PARAMS.PAGE_NUM] = [shiftid for shiftid in page_shifts if shiftid != driver_id]
            UI_PARAMS.LIST_FILTERED_SHIFT_IDS = [shiftid for shiftid in UI_PARAMS.LIST_FILTERED_SHIFT_IDS if shiftid != driver_id]
            UserParams.update(basket_shifts='|'.join([str(x) for x in basket_shifts.get_basket_shift_ids() if x != driver_id]))

            try:
                return get_chart_data()
            except Exception:
                return {'code': 400, 'message': f'Removing shift failed!: {log_exception(False)}'}
        
        return {'code': 400, 'message': f'Removing shift failed!: UI_SHIFT_DATA.remove_shift == NOK!'}

    def handle_drivers_info(self, **dct_params):
        """
        Entry point when creating new or modifying an existing shift data
        """

        __sftname1 = dct_params['driver_id']
        __sftname2 = dct_params['driver_id_2']

        _shift_id = DriversInfo.get_shift_id(shiftname=__sftname1)
        dct_params['shift_id'] = _shift_id

        if _shift_id:
            self._dct_cached_info.setdefault(
                'just_handled_shifts', set()).add(_shift_id)
            
            UI_PARAMS.update(dct_cached_info=self._dct_cached_info)

        if __sftname2 != __sftname1:

            if not DriversInfo.shiftname_taken(__sftname2):
                self._display_err(f"The name {__sftname2} is taken!")
                return {}

            return self._rename_shift(**dct_params)

        __vehicle_type = int(dct_params.get('vehicle_type', 0))

        if not _shift_id:

            try:
                # dct_params = {'page_num': 1, 'weekdays': ['Mon', 'Tue', 'Thu'], 'ctrl_by': 'KG4', 'driver_id': 'KG4.test.s1',
                #  'driver_id_2': 'KG4.test.s1', 'operator': 'FedEx Express', 'start_loc': 'KG4', 'double_man': False,
                #  'hbr': True, 'vehicle_type': '1'}

                shiftid = DriversInfo.register_new(**dct_params)

                self._dct_cached_info.setdefault(
                    'just_handled_shifts', set()).add(shiftid)

                UI_PARAMS.update(dct_cached_info=self._dct_cached_info)
                dct_params.update({'shift_id': shiftid})

                ShiftIndex.update_shift_index(
                    shiftname=dct_params['driver_id'], ctrl_loc=dct_params['ctrl_by'])

                __chart_data = self.blank_shift(**dct_params)

                return __chart_data

            except Exception:
                log_exception(
                    popup=True, remarks=f"Creating {__sftname1} failed!")

                return {}

        try:

            dct_params.update({'shift_id': _shift_id})

            # If a tour has movements, do not allow vehicle type change
            _loaded_m = UI_SHIFT_DATA.optimal_drivers.get(
                _shift_id, {}).get('list_loaded_movements', [])

            if _loaded_m:

                _vehicle = UI_SHIFT_DATA.optimal_drivers.get(
                    _shift_id, {}).get('vehicle', 0)

                if _vehicle and _vehicle != __vehicle_type:

                    self._display_err(
                        f'The vehicle type change of a non-empty shift is not permitted due to potential ' +
                        'discrepancies between the shift and its associated movements.')

                    return {}

            UI_SHIFT_DATA.update_drivers(**dct_params)
            _exception_message = UI_SHIFT_DATA.exception_message

            UI_PARAMS.OPTIONS.update(
                {'list_operators': Operator.list_operators()})

            if _exception_message != '':
                self._display_info(_exception_message)

            else:
                self._display_info(
                    f'The shift info of {_shift_id}: {__sftname1} has been successfully updated.')

            return get_chart_data()

        except Exception:
            log_exception(
                popup=True, remarks=f"Creating {_shift_id}: {__sftname1} failed!")

            return {}

    def _rename_shift(self, **dct_params):

        _shift_id = dct_params['shift_id']
        __sftname2 = dct_params['driver_id_2']
        page_num = dct_params['page_num']

        _msg = ''
        try:

            dct_params['driver_id'] = __sftname2
            dct_params.pop('driver_id_2', '')
            dct_params['shift_id'] = _shift_id

            UI_SHIFT_DATA.update_drivers(**dct_params)

            UI_SHIFT_DATA.rename_shift(
                shift_id=_shift_id, rename_to=__sftname2)

            UI_PARAMS.OPTIONS.update(
                {'list_operators': Operator.list_operators()})

            __page_drivers = UI_PARAMS.DICT_DRIVERS_PER_PAGE[page_num]
            __page_drivers.append(__sftname2)

            UI_PARAMS.LIST_FILTERED_SHIFT_IDS.append(__sftname2)
            UI_PARAMS.DICT_DRIVERS_PER_PAGE[page_num] = __page_drivers

            _msg = f"The shift {_shift_id} has been successfully renamed to {__sftname2}.\n"

        except Exception:

            log_exception(
                popup=True, remarks=f"Renaming {_shift_id} to {__sftname2} failed.")

            return {}

        _str_msg = ''

        try:
            _basket_shifts = UserParams.get_param(
                param='basket_shifts', if_null='').split('|')

            if _basket_shifts:

                if _shift_id in _basket_shifts:

                    _basket_shifts = [
                        x for x in _basket_shifts if x != _shift_id]
                    _basket_shifts.append(__sftname2)
                    UserParams.update(
                        basket_shifts='|'.join([str(x) for x in _basket_shifts]))

                    _str_msg = 'Basket has been refreshed too!'

        except Exception:
            _str_msg = 'Refreshing basket failed!'
            log_exception(
                popup=True, remarks=f"Refreshing basket to change {_shift_id} to {__sftname2} failed.")

        if _str_msg != '':
            _msg = f'{_msg}{_str_msg}'

        self._display_info(_msg)

        __chart_data = get_chart_data(**{'page_num': page_num})

        return __chart_data

    def get_driver_info(self, **dct_params):

        try:
            
            get_right_click_id = dct_params['get_right_click_id']

            if get_right_click_id:
                shift_id = UI_PARAMS.RIGHT_CLICK_ID
                UI_PARAMS.RIGHT_CLICK_ID = 0

                dct_params['driver'] = DriversInfo.get_shift_name(shift_id=shift_id)

            __dct = DriversInfo.to_sub_dict(shift_ids=[shift_id])[shift_id]

            __msg = ''
            if not __dct:

                __msg = f"No data was found in LION for {dct_params['driver']}. "
                __msg = f'{__msg}Please validate the info before saving!'

                raise ValueError(__msg)

            running_days = DriversInfo.get_shift_id_running_days(shift_id=shift_id)

            ctrl_by = __dct.get('controlled by', 'N/A')

            operatoid = __dct.get('operator', 1)
            opr = Operator.query.filter(Operator.operator_id == operatoid).first()

            if opr:
                __dct['operator'] = opr.operator

            __dct.update({'vehicle': __dct.get('vehicle', 1)})
            __dct.update({'double_man': __dct.get('double_man', False)})
            __dct.update({'hbr': __dct.get('hbr', True)})
            __dct['source'] = 'LION'
            # __dct.update({'operator': __dct.get('operator', 'FedEx Express')})
            __dct['driver'] = dct_params['driver']
            __dct.update(
                {'controlled by': __dct.get('controlled by', ctrl_by)})

            __dct.update(
                {'start position': __dct.get('start position', ctrl_by)})

            return {'data': __dct,
                    'message': __msg,
                    'weekdays': running_days}

        except Exception:

            return {'data': {},
                    'message': log_exception(popup=False, remarks='No driver info returned.'),
                    'weekdays': running_days}

    def get_driver_note(self, **dct_params):

        try:
            __driver = dct_params['driver']
            return {'message': UI_SHIFT_DATA.optimal_drivers.get(
                __driver, {}).get('shift_note', '')}

        except Exception:
            __err = log_exception(
                popup=False, remarks='Error occured while retreving driver note. ')

            return {'message': f'Error occured while retreving driver note: {__err}'}

    def save_shift_note(self, **dct_params):

        try:
            __text = dct_params['shift_note']
            __driver = dct_params['driver']
            shift_id = UI_PARAMS.RIGHT_CLICK_ID
            UI_PARAMS.RIGHT_CLICK_ID = 0

            if __driver not in __text:
                __text = f'A note on {__driver} by {
                    self._user_display_name}: {__text}'

            __existing_note = UI_SHIFT_DATA.optimal_drivers.get(shift_id, {}).get('shift_note', '')

            if __existing_note != '':
                __text = f'{__existing_note}\n{__text}'

            __text = split_string(txt=__text, line_length=120)

            UI_SHIFT_DATA.optimal_drivers[shift_id].update(
                {'shift_note': __text})

            DriversInfo.save_dct_tours(
                dct_tours={shift_id: UI_SHIFT_DATA.optimal_drivers[shift_id]})

            return get_chart_data()

        except Exception:
            log_exception(popup=True, remarks='save_shift_note failed!')
            return {}

    def refresh_unplanned_movs(self):

        try:
            objs = ShiftMovementEntry.query.filter(
                ShiftMovementEntry.shift_id == 0).all()

            if objs:
                return {obj.movement_id: UI_SHIFT_DATA.dict_all_movements[
                    obj.movement_id].loc_string for obj in objs}

        except Exception:
            log_exception(
                popup=False, remarks='refresh_unplanned_movs failed!')

        return {}

    def _refresh_dct_movement(self, m, new_dep_dt):

        try:
            __dct_m = UI_SHIFT_DATA.dict_all_movements[m]
            __dct_m.dep_date_time = new_dep_dt

            return {m: __dct_m}

        except Exception:
            log_exception(popup=False, remarks=f"Movement changes failed!")

        return __dct_m

    def change_movement_time(self, **dct_params):

        try:
            __m = int(dct_params['movement'])
            __dt = dct_params['datetime']
            __dct_m_time_changes = self._refresh_dct_movement(
                m=__m, new_dep_dt=to_lion_datetime(__dt))

            UI_SHIFT_DATA.update(
                dict_movements=__dct_m_time_changes)

        except Exception:
            log_exception(
                popup=False, remarks=f"changing movement time failed!")

            return {}

        return get_chart_data(**dct_params)

    def make_m_draggable(self, **dct_params):

        __m = int(dct_params['movement'])
        # self._movement_made_draggable = __m

        __dct_m = UI_SHIFT_DATA.dict_all_movements.get(__m, {})
        __dct_m.update({'draggableX': True})

        UI_SHIFT_DATA.update(
            dict_movements={__m: __dct_m})

        return get_chart_data(**dct_params)

    def add_movement_to_dump_area(self, list_m=[]):

        # self._dct_dump_area = {
        #     'driver': 1,
        #     'tour_id': 0,
        #     'list_loaded_movements': [],
        #     'list_movements': [],
        #     'dep_date_time': UI_SHIFT_DATA.xAxis_range_start,
        #     'arr_date_time': UI_SHIFT_DATA.xAxis_range_end,
        #     'shift_end_datetime': UI_SHIFT_DATA.xAxis_range_end
        # }

        try:
            if not list_m:
                return

            self._dct_dump_area = UI_SHIFT_DATA.dct_movement_dump_area
            _dct_movement_recycle_bin = UI_SHIFT_DATA.dct_movement_recycle_bin

            _dct_movement_recycle_bin.update(UI_SHIFT_DATA.optimal_drivers.get(
                2, {}))

            self._dct_dump_area.update(UI_SHIFT_DATA.optimal_drivers.get(
                1, {}))

            __list_tour_movements = self._dct_dump_area.get(
                'list_movements', [])

            __new_ms = [m for m in list_m if m not in __list_tour_movements]

            __list_tour_movements.extend(__new_ms)

            __loaded = [
                m for m in __list_tour_movements if self._is_loaded.is_loaded(m)]

            self._dct_dump_area.update(
                {'list_movements': __list_tour_movements})

            self._dct_dump_area['list_loaded_movements'] = __loaded

            __dct_ms = secure_copy(
                {m: UI_SHIFT_DATA.dict_all_movements[m] for m in __new_ms})

            for m in __new_ms:
                __dct_ms[m].shift_id = 1

            UI_SHIFT_DATA.update(
                dct_opt_drivers={
                    1: DctTour(**self._dct_dump_area),
                    2: DctTour(**_dct_movement_recycle_bin)},
                dict_movements=__dct_ms)

            if not SaveSchedule(impacted_movements=list_m, impacted_shifts=[1]).save_ok:

                raise ValueError(
                    'Save schedule failed when adding movemnt to dump area!')

        except Exception:
            log_message(message='The movements %s were not added to the dump area!\n%s' % (
                '-'.join([str(m) for m in list_m]), log_exception()),
                module_name='DnD.py/add_movement_to_dump_area')

    def _remove_movement_from_dump_area(self, m):

        try:
            __dct_dump_area = DctTour(
                **UI_SHIFT_DATA.optimal_drivers[1])

            __list_tour_movements = __dct_dump_area.list_movements

            if m in __list_tour_movements:
                __list_tour_movements.remove(m)

            if __list_tour_movements:
                __loaded = [
                    m for m in __list_tour_movements if self._is_loaded.is_loaded(m)]
            else:
                __loaded = []

            __dct_dump_area.update(
                {'list_movements': __list_tour_movements})

            __dct_dump_area['list_loaded_movements'] = __loaded

        except Exception:
            log_exception(popup=False)
            return

        UI_SHIFT_DATA.update(
            dct_opt_drivers={1: __dct_dump_area})

    def changed_detected(self):

        try:
            sids_to_save = [
                obj.shift_id for obj in DriversInfo.query.filter(
                    DriversInfo.data.isnot(None)).all()]

            if sids_to_save:
                return True

        except Exception:
            log_exception(popup=False)

        return False


    def accept_schedule(self, **dct_params):

        page_num = dct_params['page_num']

        try:

            UI_SHIFT_DATA.set_new_drivers = set()
            UI_SHIFT_DATA.set_removed_drivers = set()
            UI_SHIFT_DATA.set_changed_drivers = set()
            self._backup_active_shift_data_b4_optimization = None

        except Exception:
            log_exception(popup=True, remarks='accept_schedule failed!')
            return {}

        return get_chart_data(page_num=page_num)

    def reject_schedule(self, **dct_params):

        try:
            # UI_SHIFT_DATA = copy_obj(
            #     self._backup_active_shift_data_b4_optimization)

            self._backup_active_shift_data_b4_optimization = None
        except Exception:
            log_exception(popup=True, remarks='reject_schedule failed!')
            return {}

        return get_chart_data(**dct_params)

    def _load_user_resources_info(self):

        try:
            __dct_employed_by_user = Resources.dct_employed_by_user()
            __dct_subco_by_user = Resources.dct_subco_by_user()
        except Exception:
            log_exception(
                popup=False, remarks='Could not process user-provided location resources!')

            __dct_employed_by_user = {}
            __dct_subco_by_user = {}

        if not __dct_employed_by_user or is_file_updated(
                filename='Resources.xlsx', Path=LION_OPTIMIZATION_PATH):

            try:
                _pr_user_resource_file = os_path.join(
                    LION_OPTIMIZATION_PATH, 'Resources.xlsx')

                if not os_path.exists(_pr_user_resource_file):
                    raise ValueError(f'Missing file: {_pr_user_resource_file}')

                __df_user_resources = read_excel(
                    _pr_user_resource_file, sheet_name='ResourcesPerLoc')
                __df_user_resources['Total'] = __df_user_resources.apply(
                    lambda x: x['Employed'] + x['Subco'], axis=1)

                __df_user_resources = df_groupby(df=__df_user_resources,
                                                 agg_cols_dict={
                                                     'Total': 'max'},
                                                 groupby_cols=['loc_code', 'Employed', 'Subco']).copy()

                __cols = __df_user_resources.columns.tolist()
                __df_user_resources.rename(
                    columns=({c: c.lower() for c in __cols}), inplace=True)

                Resources.bulk_import_resources(df_resources=__df_user_resources)
                del __cols, __df_user_resources

                __dct_employed_by_user = Resources.dct_employed_by_user()
                __dct_subco_by_user = Resources.dct_subco_by_user()

            except Exception:
                log_exception(
                    popup=False, remarks='Could not read user-provided location resources!')

                __dct_employed_by_user = {}
                __dct_subco_by_user = {}

        return __dct_employed_by_user, __dct_subco_by_user

    def extract_locations_info(self, **dct_params):
        """
        Reads/loads Resources.xlsx file provided by user for number of
        subcontractors and employed drivers per location. Then, extracts
        similar information from the schedule and constructs a final
        loc_params table for optimization (used by MIP); when running strategic_optimization, a dataframe __df_locs_opt is returned
        to be later used for reporting number of fixed, employed and subcontractor drivers per location when dumping
        KPIs
        """

        __df_locs = DataFrame()
        _user_selected_vehicle_code = dct_params.get(
            'user_selected_vehicle_code', 0)

        try:

            if not _user_selected_vehicle_code:
                self._set_excluded_shift_ids = set()

            if not self._set_excluded_shift_ids:
                self._get_excluded_shift_ids(
                    user_selected_vehicle_code=_user_selected_vehicle_code)

            __dct_footprint = secure_copy(Location.to_dict())

            __df_locs = DataFrame.from_dict(
                __dct_footprint, orient='index')

            __df_locs['active'] = __df_locs.active.apply(lambda x: int(x))

            # Load number of subco and employed drivers per location based on current schedule
            # Moreover, specify the number of fixed (out of scope) per location based on
            # self._set_excluded_shift_ids
            __dct_loc_unfixed_employed_drivers, __dct_loc_fixed_employed_drivers, \
                __dct_loc_fixed_subco_drivers, \
                __dct_loc_unfixed_subco_drivers = self._dump_dct_drivers_per_location(
                    set_excluded_shifts=self._set_excluded_shift_ids)

            # Load number of subco and employed drivers per location based user input
            __dct_employed_by_user, __dct_subco_by_user = self._load_user_resources_info()

            # Prepare locations resource details data for optimization or report
            __df_locs['un_fixed_employed'] = __df_locs.loc_code.apply(
                lambda x: len(__dct_loc_unfixed_employed_drivers.get(x, [])))

            __df_locs['fixed_employed'] = __df_locs.loc_code.apply(
                lambda x: len(__dct_loc_fixed_employed_drivers.get(x, [])))

            __df_locs['fixed_subco'] = __df_locs.loc_code.apply(
                lambda x: len(__dct_loc_fixed_subco_drivers.get(x, [])))

            __df_locs['un_fixed_subco'] = __df_locs.loc_code.apply(
                lambda x: len(__dct_loc_unfixed_subco_drivers.get(x, [])))

            __df_locs['Employed'] = __df_locs.apply(
                lambda x: sum(x[c] for c in ['un_fixed_employed', 'fixed_employed']), axis=1)

            __df_locs['Subco'] = __df_locs.apply(
                lambda x: sum(x[c] for c in ['un_fixed_subco', 'fixed_subco']), axis=1)

            if __dct_employed_by_user:
                __df_locs['extra_employed'] = __df_locs.apply(
                    lambda x: __dct_employed_by_user.get(x['loc_code'], 0) - x['Employed'], axis=1)
            else:
                __df_locs['extra_employed'] = 0

            if __dct_subco_by_user:
                __df_locs['extra_subco'] = __df_locs.apply(
                    lambda x: __dct_subco_by_user.get(x['loc_code'], 0) - x['Subco'], axis=1)
            else:
                __df_locs['extra_subco'] = 0

            del __dct_loc_unfixed_employed_drivers, __dct_loc_fixed_employed_drivers
            del __dct_loc_fixed_subco_drivers, __dct_loc_unfixed_subco_drivers
            del __dct_employed_by_user, __dct_subco_by_user

            __df_locs['remarks'] = 'Fixed includes fixed drivers, Non-Artic and Filtered-out shifts'

        except Exception:
            log_exception(popup=True, remarks='Extracting locations failed!')
            __df_locs = DataFrame()
            return __df_locs

        if dct_params.get('dump_locs_info', False):

            try:

                xlwriter(df=__df_locs.copy(),
                         sheetname='Locations',  xlpath=os_path.join(
                    LION_LOGS_PATH, 'Locations.xlsx'))

                del __df_locs
            except Exception:
                log_exception(
                    popup=True, remarks='Dumping loc info failed!')

            log_message(
                message=f'Locations.xlsx has been dumped in {LION_LOGS_PATH}')

            return

        try:
            __opt_cols = ['loc_code', 'loc_type', 'active', 'un_fixed_employed',
                          'fixed_employed', 'fixed_subco', 'un_fixed_subco', 'extra_employed',
                          'extra_subco', 'remarks']

            self._sql_db = getattr(self, '_sql_db', SqlDb())
            __df_locs_opt = __df_locs.loc[:, __opt_cols].copy()
            __df_locs_opt['timestamp'] = datetime.now()

            self._sql_db.to_sql(dataFrame=__df_locs_opt,
                                destTableName='loc_params', ifExists='replace')

            return __df_locs_opt

        except Exception:
            log_exception(popup=True, remarks='Dumping locations failed!')
            return DataFrame()

    def extract_movements_to_process(self, **dct_params):

        self._set_excluded_shift_ids = set()
        self._set_excluded_movements = set()

        __days = dct_params.get('days', [])
        _user_selected_vehicle = int(dct_params.get(
            'vehicle_code', 0))

        __extract_all = not _user_selected_vehicle

        __days_n_scope = []

        try:

            if dct_params.get('days', []):
                __days_n_scope.extend(
                    [dy for dy in __days if dy in WEEKDAYS_NO_SAT])
            else:
                __days_n_scope.extend(WEEKDAYS_NO_SAT)

            if not __extract_all:
                self._get_excluded_shift_ids(
                    user_selected_vehicle_code=_user_selected_vehicle,
                    run_all=True)

            _all_driver_ids = set(UI_SHIFT_DATA.optimal_drivers)

            if _user_selected_vehicle:
                __filter_shifts = [x[0] for x in DriversInfo.query.with_entities(DriversInfo.shift_id).filter(
                    DriversInfo.vehicle == _user_selected_vehicle).all()]

                _all_driver_ids = [
                    d for d in _all_driver_ids if d in __filter_shifts]

            if _all_driver_ids:

                movs = ShiftMovementEntry.query.filter(
                    ShiftMovementEntry.is_loaded.in_([1, True]),
                    ShiftMovementEntry.shift_id.in_(_all_driver_ids)
                ).all()

                # if not __extract_all:
                #    movs = [mobj for mobj in movs if mobj.tu_dest == '']

            else:
                movs = []

            str_movs = ['|'.join([str(MovObj.movement_id), MovObj.str_id, MovObj.loc_string, MovObj.tu_dest, str(
                MovObj.shift_id)]) for MovObj in movs]

            df_all_movements = DataFrame([movstr.split('|') for movstr in str_movs],
                                         columns=['MovementId', 'From', 'To', 'DepDay', 'DepTime', 'VehicleType', 'TrafficType',
                                                  'loc_string', 'tu', 'shift_id'])

            df_all_movements['loc_string'] = df_all_movements.apply(lambda x: x['loc_string']
                                                                    if len(x['loc_string']) > 0 else '.'.join(
                [x['From'], x['To'], x['DepTime']]), axis=1)

            df_all_movements['VehicleType'] = df_all_movements.VehicleType.apply(
                lambda x: VehicleType.get_vehicle_name(vehicle_code=int(x)))

            df_all_movements['DepDay'] = df_all_movements['DepDay'].astype(int)
            df_all_movements['MovementId'] = df_all_movements['MovementId'].astype(
                int)

            for wkdy in __days_n_scope:

                df_all_movements[wkdy] = df_all_movements.shift_id.apply(lambda x: DriversInfo.shift_id_runs_on_weekday(
                    shift_id=int(x), weekday=wkdy))

            df_all_movements['InScope'] = ~df_all_movements.MovementId.astype(int).isin(
                self._set_excluded_movements)

            df_all_movements = df_groupby(df=df_all_movements,
                                          groupby_cols=[
                                              'loc_string', 'From', 'To', 'tu', 'DepDay',
                                              'DepTime', 'TrafficType', 'VehicleType', 'InScope'],

                                          agg_cols_dict={wkday: 'max' for wkday in __days_n_scope})

            cols = ['loc_string', 'From', 'To', 'tu', 'DepDay',
                    'DepTime', 'TrafficType', 'VehicleType', 'InScope']
            cols.extend(__days_n_scope)

            df_all_movements = df_all_movements.loc[:, cols].copy()

            df_all_movements.sort_values(
                by=['loc_string', 'DepDay', 'DepTime'], inplace=True)

            if __extract_all:
                xlpath = os_path.join(LION_LOGS_PATH, 'movements.xlsm')
            else:
                xlpath = os_path.join(LION_OPTIMIZATION_PATH, 'movements.xlsm')

            xlwriter(df=df_all_movements, sheetname='Movements',
                     xlpath=xlpath, header=False)

            del df_all_movements

        except Exception:
            log_exception(
                popup=True, remarks=f"Extracting movements failed!")

        finally:
            self._set_excluded_shift_ids = set()
            self._set_excluded_movements = set()

        return

    def populate_user_settings(self):

        try:
            return {'dct_vals': UserParams.to_dict(), 'dct_elements': UserParams.to_elem_dict()}
        except Exception:
            log_exception(popup=False,
                           remarks="Loading user params failed!")

    def set_user_param(self, **dct_params):

        _dct = {dct_params['param']: dct_params['val']}

        try:
            UserParams.update(**_dct)
        except Exception:
            self._display_err(
                f"Parameter setting failed! {log_exception(False)}")

    def set_egis_scenario(self, **dct_params):

        self._egis_scn = dct_params.get('runtimes_scenario', 'Default')
        _popupmsg = ''

        try:
            UserParams.update(runtimes_scenario=self._egis_scn)
            UI_RUNTIMES_MILEAGES.reset()

        except Exception:
            _popupmsg = log_exception(
                popup=False, remarks='setting user egis scenario failed!')

            self._egis_scn = 'Default'

        if _popupmsg == '':
            _popupmsg = 'Please reload the scenario/plan from the dropdown list to see your selected scenario take effect.'

        return {'chart_data': get_chart_data(),
                'message': _popupmsg
                }

    def get_user_param(self, param, if_null):

        try:
            return UserParams.get_param(param=param, if_null=if_null)
        except Exception:
            return None

    def load_available_vehicle_types(self):

        try:
            _dct_vehicle = VehicleType.dict_vehicle_name()
            return _dct_vehicle
        except Exception:
            log_exception(False)
            return {}

    def update_suppliers(self, **dct_params):

        try:
            UI_SHIFT_DATA.reset()
            UI_PARAMS.UPDATE_SUPPLIERS = True

        except Exception:
            return {'err': log_exception(False)}

        return {}


    def review_shifts(self, **dct_params):

        try:

            if dct_params.get('refresh_all', False):
                """
                To review and identify illegal shifts
                """
                return SHIFT_MANAGER.review_shifts()
                
            if dct_params.get('search4shift', False):

                list_m = []
                if dct_params.get('set_right_click_id', False):
                    if UI_PARAMS.RIGHT_CLICK_ID:
                        list_m.append(UI_PARAMS.RIGHT_CLICK_ID)
                        UI_PARAMS.RIGHT_CLICK_ID = 0

                msg = ''

                list_shifts2review = []
                if getattr(self, 'search_current_page_only_flag', False):
                    list_shifts2review.extend(
                        UI_PARAMS.DICT_DRIVERS_PER_PAGE[UI_PARAMS.PAGE_NUM])
                else:
                    list_shifts2review.extend(UI_PARAMS.LIST_FILTERED_SHIFT_IDS)

                if not list_shifts2review:
                    raise Exception('No shift was selected to evaluate!')

                get_shift_proposals(shifts2review=list_shifts2review, list_m=list_m)

                __notifications = SHIFT_MANAGER.notifications

                if __notifications:
                    return {'code': 200, 'message': f'{__notifications}{msg}'}

                return {'code': 400, 'message': SHIFT_MANAGER.exception_message}

            __currPageOnly = dct_params['currPageOnly']
            page_num = dct_params['page_num']
            __drivers = dct_params.get('drivers', [])

            if not __drivers:
                if __currPageOnly:
                    __drivers = UI_PARAMS.DICT_DRIVERS_PER_PAGE[page_num]

            SHIFT_MANAGER.review_shifts(list_of_tours=__drivers)

            __msg = SHIFT_MANAGER.exception_message

            if __msg == '':
                __msg = 'Repair completed successfully!'

            self._display_info(__msg)
            return get_chart_data(**dct_params)

        except Exception:

            log_exception(popup=True)
            return get_chart_data(**dct_params)

    def _display_info(self, message):
        try:
            show_popup(mytitle='Info', message=message)
        except Exception:
            log_exception(False)

    def _display_err(self, message):
        try:
            show_error(message=message)
        except Exception:
            log_exception(False)

    def set_right_click_id(self, **dct_params):

        point_id = dct_params.get('point_id', None)
        try:
            point_id = int(point_id)
        except Exception:
            log_exception(popup=False)
            point_id = 0

        UI_PARAMS.RIGHT_CLICK_ID = point_id

    def refresh_shift_index(self, **dct_params):

        try:
            ShiftIndex.refresh_indices()
            UI_SHIFT_DATA.refresh_dct_shift_ids_per_loc_page()
        except Exception:
            self._display_err(f'clear_shift_index failed! {log_exception(False)}')

            return {}

        self._display_info(
            message='Shift indices updated successfully! Reboot LION to see the effect!')
        return {}

    def get_flow_data(self, **dct_params):

        loc_code = dct_params.get('loc_code', 'ZFC')
        hide_stn = dct_params.get('hide_stn', False)
        hide_hub = dct_params.get('hide_hub', False)
        hide_customers = dct_params.get('hide_customers', False)

        shift_ids = self._dct_vis_data_footprint.get('shift_ids', [])
        list_str_ids = self._dct_vis_data_footprint.get('list_str_ids', [])

        if not shift_ids or not shift_ids:

            shift_ids = [d for d, in DriversInfo.query.filter(
                DriversInfo.wed == 1).with_entities(DriversInfo.shift_id).all()]

            self._dct_vis_data_footprint['shift_ids'] = shift_ids

            list_str_ids = [strid[0] for strid in ShiftMovementEntry.query.filter(
                ShiftMovementEntry.is_loaded.in_([1, True]),
                ShiftMovementEntry.shift_id.in_(shift_ids),
            ).with_entities(ShiftMovementEntry.str_id).all()]

            self._dct_vis_data_footprint['list_str_ids'] = list_str_ids

        try:
            top_lanes = int(dct_params.get('top_lanes', '10').strip())
        except:
            top_lanes = 10

        try:

            set_str_ids = self._dct_vis_data_footprint.get(
                f'set_str_ids_{loc_code}', set())
            if not set_str_ids:
                set_str_ids = set(
                    [strid for strid in list_str_ids if strid.startswith(f"{loc_code}|")])
                self._dct_vis_data_footprint[f'set_str_ids_{loc_code}'] = set_str_ids

            if hide_stn:
                set_str_ids = [strid for strid in set_str_ids if Location.to_dict().get(
                    strid.split('|')[1], {}).get('loc_type', '').lower() not in ['station', 'depot']]

            if hide_hub:
                set_str_ids = [strid for strid in set_str_ids if Location.to_dict().get(
                    strid.split('|')[1], {}).get('loc_type', '').lower() not in ['hub']]

            if hide_customers:
                set_str_ids = [strid for strid in set_str_ids if Location.to_dict().get(
                    strid.split('|')[1], {}).get('loc_type', '').lower() not in ['customer']]

            lanes = ['.'.join(strid.split('|')[:2]) for strid in set_str_ids]
            dct_lanes = {loc: lanes.count(loc) for loc in set(lanes)}

            n_total_lanes = len(lanes)

            dct_lanes = dict(
                sorted(dct_lanes.items(), key=lambda x: x[1], reverse=True))
            lanes_to_disp = list(dct_lanes)[:top_lanes]

            maxVal = max(dct_lanes.values())
            min_range = 10
            max_range = 100

            def get_weight(loc):
                cnt = dct_lanes.get(loc, 0)
                mapped_value = min_range + \
                    (cnt / maxVal) * (max_range - min_range)
                return int(mapped_value)

            lanes_data = []
            all_locs = set()
            for locstring in lanes_to_disp:

                loc1, loc2 = locstring.split('.')
                all_locs.update([loc1, loc2])

                weight = get_weight(locstring)

                lanes_data.append({
                    'from': loc1,
                    'to': loc2,
                    'weight': weight,
                    'growTowards': True,
                    'fillColor': '#FF6600' if weight >= 70 else '#0099CC',
                    'fillOpacity': 0.4 if weight >= 70 else (0.2 if weight >= 40 else 0.1),
                    'color': '#FF6600' if weight >= 70 else '#0099CC',
                    'markerEnd': {
                        'width': '70%',
                        'height': '70%',
                    },
                })

        except Exception:
            log_exception(popup=False, remarks='Getting flow data failed!')
            lanes_data = []
            all_locs = set()

        return {'lanes_data': lanes_data, 'locs': list(all_locs), 'n_total_lanes': n_total_lanes}


DRIVERS_UI = DriversUI.get_instance()