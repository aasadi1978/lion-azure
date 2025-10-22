from collections import defaultdict
from datetime import datetime, timedelta
import logging

from lion.config.libraries import OS_PATH
from lion.config.paths import LION_DIAGNOSTICS_PATH, LION_LOGS_PATH
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.orm.scn_info import ScnInfo
from lion.ui.ui_params import UI_PARAMS
from lion.utils.safe_copy import secure_copy
from lion.utils.df2csv import export_dataframe_as_csv
from lion.utils.combine_date_time import combine_date_time
from lion.logger.exception_logger import log_exception
from pandas import DataFrame
from lion.orm.drivers_info import DriversInfo
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.movement.dct_movement import DictMovement
from lion.tour.dct_tour import DctTour
from lion.utils.dict2class import Dict2Class
from lion.utils.minutes2hhmm import minutes2hhmm
from lion.logger.status_logger import log_message, log_message
from lion.bootstrap.constants import LION_DATES, MOVEMENT_DUMP_AREA_NAME, RECYCLE_BIN_NAME, LOC_STRING_SEPERATOR
from lion.utils.is_loaded import IsLoaded
from lion.orm.shift_index import ShiftIndex
from lion.orm.user_params import UserParams
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from sqlalchemy.exc import SQLAlchemyError
from lion.tour.cost import TourCost
from lion.xl.write_excel import write_excel as xlwriter


class ShiftData():

    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self):
        pass

    def initialize(self):

        if self._initialized:
            return
        
        try:
            logging.info(f"Initializing global UI_SHIFT_DATA ...")
            self.clean_initialization_shift_data()

            self.__scn_name = ScnInfo.scn_name()
            self.__n_drivers_per_page = UserParams.get_param(param='page_size')
            self.__xAxis_range_start = UserParams.get_param(
                param='xAxis_range_start', if_null=combine_date_time(
                    LION_DATES[self.__weekday], '0000'))

            self.__xAxis_range_end = UserParams.get_param(param='xAxis_range_end', if_null=combine_date_time(
                LION_DATES[self.__weekday] + timedelta(days=1), '2300'))

            if type(self.__xAxis_range_start) == str:
                self.__xAxis_range_start = datetime.strptime(
                    self.__xAxis_range_start, "%Y-%m-%d %H:%M:%S")

            if type(self.__xAxis_range_end) == str:
                self.__xAxis_range_end = datetime.strptime(
                    self.__xAxis_range_end, "%Y-%m-%d %H:%M:%S")

            self.__dct_movement_dump_area = DctTour(**{
                    'shift_id': 1,
                    'driver': MOVEMENT_DUMP_AREA_NAME,
                    'tour_id': 0,
                    'list_loaded_movements': [],
                    'list_movements': [],
                    'list_tour_movements_with_breaks': [],
                    'dep_date_time': self.__xAxis_range_start,
                    'arr_date_time': self.__xAxis_range_end,
                    'shift_end_datetime': self.__xAxis_range_end,
                    'tour_loc_string': '',
                    'is_fixed': False,
                    'dct_running_tour_data': {}
                })

            self.__dct_movement_dump_area.update({
                'tour_cntry_from': UI_PARAMS.LION_REGION,
                'is_complete': False,
                'tour_loc_from': '',
                'total_dur': 0,
                'tour_repos_dist': 0,
                'tour_input_dist': 0,
                'driving_time': 0,
                'input_driving_time': 0,
                'repos_driving_time': 0,
                'idle_time': 0,
                'is_feas': True,
                'is_fixed': False,
                'Source': 'LION',
                'remark': '',
                'notifications': '',
                'mouseover_info': '',
                'avg_utilisation': 0.01,
                'time_utilisation': 0,
                'n_repos_movs': 0,
                'n_input_movs': 0,
                'vehicle': 0,
                'interim_idle_times': [],
                'weekday': 1,  # 1 for Monday ... 5 for Friday
                'double_man': False
            })

            self.__dct_movement_recycle_bin = secure_copy(
                self.__dct_movement_dump_area)

            self.__dct_movement_recycle_bin.update(
                {'driver': RECYCLE_BIN_NAME, 'tour_id': 2, 'shift_id': 2})
            
            self._initialized = True
            logging.info(f"UI_SHIFT_DATA initialized successfully.")

        except Exception:
            log_exception('ShiftData was not initialized!')

    def reset(self):
        self._initialized = False
        self.initialize()

    @classmethod
    def get_instance(cls):
        return cls()
    
    def clean_initialization_shift_data(self, weekday='Mon'):

        try:
            self.__dct_missing_used_movements = defaultdict(set)
            self.__list_loaded_planned_loc_string = []
            self.__dct_changeover_shifts = {}
            self.__is_loaded = IsLoaded()
            self.__dct_modified_optimal_drivers = {}
            self.__optimal_drivers_backup = {}
            self.__optimal_drivers = {}
            self.__dct_changeovers = {}
            self.__dct_drivers = {}
            self.__dct_max_n_drivers_per_loc = {}
            self.__dct_shift_ids_per_loc_page = {}
            self.__dct_unplanned_movements = {}
            self.__weekday = weekday
            self.__user_note = ''
            self.__exception_message = ''
            self.__dblman_shifts = []
            self.__dct_movement_leg = defaultdict(dict)
            self.__dct_movement_tu = defaultdict(dict)
            self.__n_drivers_per_page = 15

            self.__xAxis_range_noon_start = combine_date_time(
                    LION_DATES[self.__weekday], '1200')

            self.__xAxis_range_noon_end = combine_date_time(
                    LION_DATES[self.__weekday] + timedelta(days=1), '1200')

        except Exception:
            log_exception(
                    popup=True, remarks='ShiftData could not be initialised!')

    @property
    def dct_missing_used_movements(self):
        """
        return a dict with shift in keys and set of missing movements in values
        """
        if not self.__dct_missing_used_movements:
            self.__get_set_used_movements()

        return dict(self.__dct_missing_used_movements)

    @property
    def set_movement_dump_movements(self):

        try:
            __set_dump_area_movs = set(
                self.__optimal_drivers.get(1, {}).get('list_loaded_movements', []))

        except Exception:
            log_exception(
                popup=True, remarks='set_movement_dump_movements failed!')

            return set()

        return __set_dump_area_movs

    @property
    def dct_unplanned_movements(self):

        try:
            if not self.__dct_unplanned_movements or not self.__list_loaded_planned_loc_string:
                self.extract_dct_unplanned_movements(
                    get_planned_loc_string=True)

            if not self.__dct_unplanned_movements:
                return {}

            __set_dump_area_movs = set(
                self.__optimal_drivers.get(1, {}).get('list_loaded_movements', []))

            for m in __set_dump_area_movs:
                self.__dct_unplanned_movements.pop(m, {})

            _loaded_unplanned_movs = list(self.__dct_unplanned_movements)
            _dct_loaded_unplanned_loc_string = {}

            _loc_strings = []
            for m in _loaded_unplanned_movs:
                dct_m = self.__dct_unplanned_movements.get(m, {})
                if dct_m:
                    loc_str = '.'.join(
                        [dct_m['From'], dct_m['To'], dct_m['DepDateTime'].strftime('%H%M')])
                    _loc_strings.append(loc_str)
                    _dct_loaded_unplanned_loc_string.update({m: loc_str})

            list_planned_locstr = [x[0]
                                   for x in self.__list_loaded_planned_loc_string]

            _list_loaded_unplanned_m_to_remove = [
                m for m, locstr in _dct_loaded_unplanned_loc_string.items()
                if locstr in list_planned_locstr]

            dct_removed = {m: v for m, v in self.__dct_unplanned_movements.items(
            ) if m in _list_loaded_unplanned_m_to_remove}

            for m in _list_loaded_unplanned_m_to_remove:
                self.__dct_unplanned_movements.pop(m, {})

            if dct_removed:

                __df_removed_movs = DataFrame.from_dict(
                    dct_removed, orient='index')

                __df_removed_movs = __df_removed_movs.loc[:, [
                    'From', 'To', 'DepDateTime', 'shift', 'loc_string']].copy()
                __df_removed_movs['DepTime'] = __df_removed_movs.DepDateTime.apply(
                    lambda x: x.strftime('%a %H:%M'))

                __df_removed_movs['linehaul_id'] = __df_removed_movs.apply(
                    lambda x: '.'.join([x['From'], x['To'], x['DepDateTime'].strftime('%H%M')]), axis=1)

                __df_removed_movs = __df_removed_movs.loc[:, [
                    'loc_string', 'linehaul_id', 'From', 'To', 'DepTime', 'shift']].copy()

                __df_removed_movs['updated_at'] = datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')

                __df_removed_movs.sort_values(by=['loc_string'], inplace=True)

                export_dataframe_as_csv(dataframe=__df_removed_movs.copy(),
                       csv_file_path=f'{
                           self.__weekday}-removed_movements_from_movement_bucket.csv',
                       FileDestination=LION_LOGS_PATH)

        except Exception:
            log_exception(
                popup=True, remarks='dct_unplanned_movements could not be calculated!')

            self.__dct_unplanned_movements = {}

        return self.__dct_unplanned_movements

    @property
    def dct_changeover_shifts(self):
        if not self.__dct_changeover_shifts:
            self.refresh_dct_movement_shift()

        return self.__dct_changeover_shifts

    @property
    def dct_movement_dump_area(self):
        return self.__dct_movement_dump_area

    @property
    def dct_movement_recycle_bin(self):
        return self.__dct_movement_recycle_bin

    @property
    def exception_message(self):
        return self.__exception_message

    @property
    def dct_modified_optimal_drivers(self):
        return self.__dct_modified_optimal_drivers

    @dct_modified_optimal_drivers.setter
    def dct_modified_optimal_drivers(self, x):
        self.__dct_modified_optimal_drivers = x

    @property
    def blank_shifts(self):

        try:
            __set_shifts = set(self.__optimal_drivers)
            __empty_shifts_ids = [d for d in __set_shifts
                                  if not self.__optimal_drivers[d].get('list_loaded_movements', [])]

            __empty_shifts_ids = [d for d in __empty_shifts_ids if d not in [
                1, 2]]

            return __empty_shifts_ids

        except Exception:
            log_exception(popup=False)

        return []

    @property
    def optimal_drivers_backup(self):
        return self.__optimal_drivers_backup

    @optimal_drivers_backup.setter
    def optimal_drivers_backup(self, x):
        self.__optimal_drivers_backup = x

    @property
    def dct_changeovers(self):
        return self.__dct_changeovers

    @dct_changeovers.setter
    def dct_changeovers(self, __dct_changeovers):
        self.__dct_changeovers = __dct_changeovers


    @property
    def dct_fixed_optimal_drivers(self):
        return {d: v for d, v in self.__optimal_drivers.items()
                if v['is_fixed'] and d not in [1, 2]}

    @property
    def optimal_drivers(self):
        return self.__optimal_drivers

    @optimal_drivers.setter
    def optimal_drivers(self, x):

        try:
            self.__optimal_drivers = x

            self.__dct_movement_recycle_bin.update({
                'driver': RECYCLE_BIN_NAME,
                'shift_id': 2,
                'dep_date_time': self.__xAxis_range_start,
                'arr_date_time': self.__xAxis_range_end,
                'shift_end_datetime': self.__xAxis_range_end,
            })

            self.__dct_movement_dump_area.update({
                'driver': MOVEMENT_DUMP_AREA_NAME,
                'shift_id': 1,
                'dep_date_time': self.__xAxis_range_start,
                'arr_date_time': self.__xAxis_range_end,
                'shift_end_datetime': self.__xAxis_range_end,
            })

            if not self.__optimal_drivers.get(1, {}).get(
                    'dep_date_time', None):

                self.__dct_movement_dump_area.update(
                    self.__optimal_drivers.get(1, {}))

                self.__optimal_drivers.update({
                    1: DctTour(**self.__dct_movement_dump_area)})

            if not self.__optimal_drivers.get(2, {}).get(
                    'dep_date_time', None):

                self.__dct_movement_recycle_bin.update(
                    self.__optimal_drivers.get(2, {}))
                self.__optimal_drivers.update({
                    2: DctTour(**self.__dct_movement_recycle_bin)})

            if not self.__optimal_drivers_backup:
                self.__optimal_drivers_backup = secure_copy(x)

        except Exception:
            log_exception(
                popup=False, remarks='optimal_drivers could not be set')

    @property
    def dict_all_movements(self) -> dict:
        """
        Returns a dictionary containing all movement data.
        This method retrieves the complete dict of movement information from the UI_MOVEMENTS object.

        Returns:
            UI_MOVEMENTS.dict_all_movements
        """
        return UI_MOVEMENTS.dict_all_movements

    @property
    def xAxis_range_noon_start(self):
        return self.__xAxis_range_noon_start

    @property
    def xAxis_range_noon_end(self):
        return self.__xAxis_range_noon_end

    @property
    def xAxis_range_start(self):
        return self.__xAxis_range_start

    @property
    def xAxis_range_end(self):
        return self.__xAxis_range_end

    @property
    def dblman_shifts(self):
        if not self.__dblman_shifts:
            self.__dblman_shifts = [d for d in self.__optimal_drivers
                                    if self.__optimal_drivers[d].get('double_man', False)]
        return self.__dblman_shifts

    @property
    def dct_shift_strings(self):

        try:
            __set_shifts = set(self.__optimal_drivers)
            __set_shifts.discard(1)
            __set_shifts.discard(2)

            return {self.__optimal_drivers[s]['driver']:  self.__optimal_drivers[s]['shift_id']
                    for s in __set_shifts}

        except Exception:
            log_exception(
                popup=False, remarks='dct_shift_strings could not be generated!')

            return {}

    @property
    def dct_loc_string(self):

        def get_shift_ids(m, loc_string):
            try:
                shiftids = ShiftMovementEntry.changeover_shift_ids(
                    loc_string=loc_string) if ShiftMovementEntry.is_changeover(loc_string) else [self.dict_all_movements[m]['shift_id']]
                
            except Exception:
                shiftids = []

            return shiftids

        try:
            __drivers = set(self.__optimal_drivers)

            __dct_drivers_movs = {d: self.__sort_list_movements(list_of_movs=self.__optimal_drivers[d].list_movements) for d in __drivers}

            return {
                f'{self.__optimal_drivers[d].driver}: {self.dict_all_movements[m].loc_string}': get_shift_ids(m, self.dict_all_movements[m].loc_string)
                for d in __drivers 
                for m in __dct_drivers_movs[d]
            }

        except Exception:

            log_exception(
                popup=False, remarks='dct_loc_string could not be generated!')

            return {}

    @property
    def set_planned_loaded_movements(self):

        try:
            __set_loaded_planned_movs = set()
            __list_drivers = list(self.__optimal_drivers)

            while __list_drivers:

                __set_loaded_planned_movs.update(
                    self.__optimal_drivers[__list_drivers.pop()]['list_loaded_movements'])

            __set_loaded_planned_movs_nodata = [m for m in
                                                __set_loaded_planned_movs if m not in self.dict_all_movements]

            if __set_loaded_planned_movs_nodata:

                str_m = '\n'.join([str(m)
                                  for m in __set_loaded_planned_movs_nodata])

                log_message(message=f"There are {len(
                    __set_loaded_planned_movs_nodata)} movements used in shifts but missing in movements set!:\n{str_m}")

                for m in __set_loaded_planned_movs_nodata:
                    __set_loaded_planned_movs.remove(m)

            return __set_loaded_planned_movs

        except Exception:
            log_exception(
                popup=False, remarks='set_planned_loaded_movements could not be generated!')

            return set()

    @property
    def weekday(self):
        return self.__weekday

    @weekday.setter
    def weekday(self, x):
        self.__weekday = x

        self.__xAxis_range_start = combine_date_time(
            LION_DATES[self.__weekday], '0300')

        self.__xAxis_range_noon_start = combine_date_time(
            LION_DATES[self.__weekday], '1200')

        self.__xAxis_range_end = combine_date_time(
            LION_DATES[self.__weekday] + timedelta(days=1), '2300')

        self.__xAxis_range_noon_end = combine_date_time(
            LION_DATES[self.__weekday] + timedelta(days=1), '1200')

    @property
    def user_note(self):
        return self.__user_note

    @user_note.setter
    def user_note(self, x):
        self.__user_note = x

    @property
    def scn_name(self):
        return self.__scn_name

    @scn_name.setter
    def scn_name(self, scn):
        self.__scn_name = scn

    @property
    def dct_shift_ids_per_loc_page(self):
        """
        self.__dct_shift_ids_per_loc_page = {loc1: {1: [drvr1, drvr2, ...], 2: [drvr3, drvr4, ...]},
                                               loc2: {1: [drv1, drv2, ...], 2: [drv3, drv4, ...]},
                                               ...}
        """

        if not self.__dct_shift_ids_per_loc_page:
            self.refresh_dct_shift_ids_per_loc_page()

        return self.__dct_shift_ids_per_loc_page

    @property
    def dct_max_n_drivers_per_loc(self):
        if not self.__dct_max_n_drivers_per_loc:
            self.__refresh_dct_max_n_drivers_per_loc()

        return self.__dct_max_n_drivers_per_loc

    @property
    def set_used_movements(self):
        self.__exception_message = ''
        return self.__get_set_used_movements()


    def clean_up_changeovers_with_unknown_movs(self):
        """
        Sometimes there are some changeovers with unknown movements which could be caused by wrong action by user.
        We run this module instead of self.__process_chgovers() to clean up those changeovers. We cannot use it as part of
        regular self.__process_chgovers() as it causes issues when creating new changeovers
        """
        self.__process_chgovers(clean_up_changeovers_with_unknown_movs=True)

    def __process_chgovers(self, clean_up_changeovers_with_unknown_movs=False, changeover_id=0):

        if changeover_id:
            if self.__dct_changeovers.get(changeover_id, {}):
                set_co_ids = set([changeover_id])
        else:
            set_co_ids = set(self.__dct_changeovers)

        if not set_co_ids:
            return

        if not self.__dct_movement_leg:
            self.__dct_movement_leg = defaultdict(dict)
            self.__dct_movement_tu = defaultdict(dict)

        try:

            if not self.__dct_changeovers:
                raise ValueError('__dct_changeovers was empty!')

            for idx in set_co_ids:

                try:
                    __loc_str = self.__dct_changeovers[idx].get(
                        'loc_string', '')

                    __loc_str = __loc_str.replace('..', '.')

                    if __loc_str != '':
                        self.__dct_changeovers[idx].update({
                            'tu': __loc_str.split('.')[-2],
                            'loc_string': __loc_str})
                    else:
                        self.__dct_changeovers.pop(idx)

                except Exception:
                    pass

            set_co_ids = [cid for cid in set_co_ids
                          if cid in self.__dct_changeovers]

            for chid in set_co_ids:

                if self.__dct_changeovers.get(chid, {}):

                    __tu = self.__dct_changeovers[chid].get('tu', '')
                    locstr = self.__dct_changeovers[chid].get('loc_string', '')

                    __legs = [lg for lg in set(
                        self.__dct_changeovers[chid]) if lg in range(10)]

                    __n = len(__legs)

                    list_shifts = []
                    list_movs = []

                    for leg in __legs:
                        __mov = self.__dct_changeovers[chid][leg]

                        if __mov in self.dict_all_movements.keys():

                            self.__dct_movement_leg.update(
                                {__mov: '%d/%d' % (leg, __n)})

                            list_shifts.append(
                                self.dict_all_movements[__mov]['shift'])

                            list_movs.append(__mov)

                            self.__optimal_drivers[
                                self.dict_all_movements[
                                    __mov]['shift_id']].update({'co_loc_string': locstr})

                            self.__dct_movement_tu.update(
                                {__mov: __tu})

                            if len(list_shifts) == len(__legs):

                                self.__dct_changeovers[chid].update({
                                    'list_shifts': list_shifts})

                                for m in list_movs:
                                    self.dict_all_movements[m].update_items(
                                        **{'ChgOverShifts': '/'.join(list_shifts),
                                           'changeover_id': chid})
                            else:
                                self.__dct_changeovers.pop(chid, {})

                        else:
                            if clean_up_changeovers_with_unknown_movs:
                                self.__dct_changeovers.pop(chid, {})
                                break
                else:
                    self.__dct_changeovers.pop(chid, {})

        except Exception:
            self.__exception_message = log_exception(False)
            return

    def update(self, dct_opt_drivers={}, dict_movements={}):

        try:
            if dict_movements:

                for mov, __dct_m in dict_movements.items():
                    if isinstance(__dct_m, dict):
                        dict_movements[mov] = DictMovement(**__dct_m)

                self.dict_all_movements.update(dict_movements)

            if dct_opt_drivers:

                for d in set(dct_opt_drivers):

                    if isinstance(dct_opt_drivers[d], dict):
                        dct_opt_drivers[d] = DctTour(**dct_opt_drivers[d])

                for d in set(dct_opt_drivers):

                    movs = dct_opt_drivers[d].list_movements
                    for m in movs:
                        self.dict_all_movements[m].shift_id = d

                    self.__optimal_drivers.update({d: dct_opt_drivers[d]})

        except Exception:
            self.__exception_message = log_exception(
                popup=False, remarks='Updating shift_data failed!')

    def __get_set_used_movements(self):

        try:
            __shiftsids = list(self.__optimal_drivers.keys())
            _set_all_movements = set(self.dict_all_movements)
            _set_shifts_with_missing_movs = set()
            self.__dct_missing_used_movements = defaultdict(set)
            __str_drivers = ''

            try:
                __shiftsids.remove(1)
            except:
                pass

            try:
                __shiftsids.remove(2)
            except:
                pass

            if __shiftsids:
                __set_used_movements = set()

                for shiftid in __shiftsids:

                    try:
                        _movs = self.__optimal_drivers[shiftid].list_movements
                        __set_used_movements.update(_movs)

                        for m in _movs:

                            if m not in _set_all_movements:
                                self.__dct_missing_used_movements[shiftid].update([
                                                                                  m])
                                _set_shifts_with_missing_movs.update([
                                    DriversInfo.get_shift_name(shift_id=shiftid)])

                    except Exception:
                        log_exception(popup=False, remarks=f"{shiftid} failed")

                if self.__dct_missing_used_movements:

                    txtpath = OS_PATH.join(
                        LION_DIAGNOSTICS_PATH, '%s-shiftnames with missing movements.txt' % self.__weekday)

                    __set_missing_used_movements = set()

                    for shftid in self.__dct_missing_used_movements:
                        __set_missing_used_movements.update(
                            self.__dct_missing_used_movements[shftid])

                    if __set_missing_used_movements:

                        self.__exception_message = f'{
                            len(__set_missing_used_movements)} movements missing in the database!\nSee {txtpath}'

                        [__set_used_movements.remove(
                            m) for m in __set_missing_used_movements]

                        __str_drivers = ''

                        for d in _set_shifts_with_missing_movs:
                            __str_drivers = f'{__str_drivers}{d}\n'

                        with open(txtpath, 'w',
                                  errors="ignore", encoding="utf8") as __f:
                            __f.writelines(__str_drivers)

                return __set_used_movements

        except Exception:
            self.__exception_message = f"{
                self.__exception_message}{log_exception(False)}"

        return set()

    def __clean_up_unused_movements(self):

        try:
            __set_used_movements = self.__get_set_used_movements()

            __set_unused_movs = [
                m for m in self.dict_all_movements.keys() if m not in __set_used_movements]

            while __set_unused_movs:
                self.dict_all_movements.pop(__set_unused_movs.pop(), None)

            del __set_used_movements

        except Exception:
            self.__exception_message = log_exception(
                remarks='Cleaning up unused movs failed!', popup=False)

    def remove_movement_from_dump_area(self, m):

        try:
            __dct_dump_area = self.__optimal_drivers[
                1]

            __list_tour_movements = __dct_dump_area['list_movements']

            if m in __list_tour_movements:
                __list_tour_movements.remove(m)

            if __list_tour_movements[1:]:
                __loaded = [
                    m for m in __list_tour_movements[1:] if self.__is_loaded.is_loaded(m)]
            else:
                __loaded = []

            __dct_dump_area.update(
                {'list_movements': __list_tour_movements})

            __dct_dump_area['list_loaded_movements'] = __loaded

        except Exception:
            log_exception(popup=False)
            return

        try:
            self.__optimal_drivers[1] = __dct_dump_area
        except Exception:
            log_exception(popup=False)
            return

    def __clean_up_empty_shifts(self):

        try:
            __set_shifts = set(self.__optimal_drivers)
            __set_shifts.discard(MOVEMENT_DUMP_AREA_NAME)
            __set_shifts.discard(RECYCLE_BIN_NAME)

            __list = [d for d in __set_shifts if not self.__optimal_drivers[
                d]['list_loaded_movements']]

            if __list:
                [self.__optimal_drivers.pop(d) for d in __list]

                if len(self.__optimal_drivers) < len(__set_shifts):
                    self.update(dct_opt_drivers=self.__optimal_drivers,
                                dict_movements=self.dict_all_movements)

        except Exception:
            self.__exception_message = log_exception(
                remarks='Cleaning up empty shifts failed!', popup=False)

    def copy_me(self):
        return self.dict_all_movements, self.__optimal_drivers, self.__dct_modified_optimal_drivers

    def remove_shift(self, shift_id=0):

        try:

            if self.__optimal_drivers.pop(shift_id, {}):
                DriversInfo.query.filter(DriversInfo.shift_id == shift_id).delete()
                LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:

            LION_SQLALCHEMY_DB.session.rollback()
            log_exception(
                popup=False, remarks=f'remove_shift {shift_id} failed!: {str(err)}')
            
            return 'NOK'

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception(
                popup=False, remarks=f'remove_shift {shift_id} failed!')
            
            return 'NOK'

        return 'OK'

    def store_modified_shifts(self, drivers):

        try:
            if not self.__optimal_drivers_backup:
                raise ValueError('No backup schedule was found!')

            drivers = [d for d in drivers if d not in [
                1, 2]]

            drivers = [
                d for d in drivers if d not in self.__dct_modified_optimal_drivers]

            if drivers:

                self.__dct_modified_optimal_drivers.update({
                    d: v for d, v in self.__optimal_drivers_backup.items() if d in drivers
                })

        except Exception:
            log_exception(
                popup=False, remarks='store_modified_shifts failed!')

    def restore_optimal_drivers_backup(self):
        self.__optimal_drivers.update(self.__optimal_drivers_backup)

    def update_optimal_drivers_backup(self, shift_id=''):

        if shift_id not in self.__optimal_drivers_backup:
            if shift_id in self.__optimal_drivers:
                self.__optimal_drivers_backup.update(
                    {shift_id: self.__optimal_drivers[shift_id]})

    def rename_shift(self, shift_id=0, rename_to=''):

        try:

            if shift_id in self.__optimal_drivers:

                __dct_rename = self.__optimal_drivers.pop(shift_id, {})
                __dct_rename.update(
                    {'driver': rename_to, 'shiftname': rename_to})
                self.__optimal_drivers.update({shift_id: __dct_rename})

                __list_loaded_movements = __dct_rename['list_loaded_movements']

                for m in __list_loaded_movements:
                    self.dict_all_movements[m].update_items(
                        **{'shift': rename_to})

        except Exception:
            log_exception(
                popup=False, remarks='rename_shift failed!')

    def blank_shift(self, shift_id):

        try:

            self.__dct_drivers = DriversInfo.to_dict()
            self.__optimal_drivers.pop(shift_id, {})

            blank_shift = {shift_id: DctTour(**{
                'driver': self.__dct_drivers.get(shift_id, {}).get('shiftname', 'Unknown'),
                'shift_id': shift_id,
                'list_loaded_movements': [],
                'tour_loc_from': self.__dct_drivers.get(shift_id, {}).get('start position', 'Unknown'),
                'tour_loc_string': '',
                'list_movements': [],
                'dep_date_time': self.xAxis_range_noon_start,
                'arr_date_time': self.__xAxis_range_noon_end,
                'shift_end_datetime': self.__xAxis_range_noon_end,
                'driver_loc_mov_type_key': '',
                'is_fixed': False,
                'double_man':  self.__dct_drivers.get(shift_id, {}).get('double_man', False),
                'vehicle': int(self.__dct_drivers.get(shift_id, {}).get('vehicle', 1))
            })}

            self.__optimal_drivers.update(blank_shift)

        except Exception:
            log_exception(
                popup=False, remarks='blank_shift failed!')

            return {}

        return blank_shift[shift_id]

    def get_fixed_movements(self, vehicle=None, filtered_shift=[]):
        """
        Note that this returns all fixed movements including empty ones
        """

        self.__dct_drivers = DriversInfo.to_dict()

        try:

            __set_drivers = set(self.__optimal_drivers)
            __set_fixed_drivers = set([
                d for d, v in self.__optimal_drivers.items() if v['is_fixed']])

            if filtered_shift:
                __set_fixed_drivers.update([
                    d for d in __set_drivers if d not in filtered_shift])

            if vehicle:
                __set_fixed_drivers.update([d for d in __set_drivers if
                                            self.__dct_drivers.get(d, {}).get('vehicle', 0) != vehicle])

            set_fixed_moves = set()
            set_fixed_loaded_moves = set()
            for d in __set_fixed_drivers:
                set_fixed_moves.update(
                    self.__optimal_drivers[d]['list_movements'])

                set_fixed_loaded_moves.update(
                    self.__optimal_drivers[d]['list_loaded_movements'])

            return Dict2Class({'all_movements': set_fixed_moves,
                               'loaded': set_fixed_loaded_moves,
                               'empty': set([x for x in set_fixed_moves if x not in set_fixed_loaded_moves])})

        except Exception:
            log_exception(False)
            return Dict2Class({'all_movements': set(),
                               'loaded': set(),
                               'empty': set()})

    def delete_changeovers(self, cids=[], loc_string=[]):

        if loc_string:
            cids = []
            for loc_str in loc_string:
                cids.extend([i for i, v in self.__dct_changeovers.items() if v.get(
                    'loc_string', '') == loc_str])

        try:
            __err = ''
            for id in cids:

                try:
                    self.__dct_changeovers.pop(id)
                except Exception:
                    __err = __err + log_exception(False)

            self.__dct_movement_leg = {}
            self.__process_chgovers()
            self.__refresh_m_leg()
            self.refresh_dct_movement_shift()

        except Exception:
            __err = __err + log_exception(False)
            return __err

        return ''

    def delete_movement(self, m):

        try:
            dct_m = self.dict_all_movements.pop(m, {})

            if dct_m:

                dct_m.shift = RECYCLE_BIN_NAME
                dct_m.shift_id = 2
                dct_m.update_str_id()
                ShiftMovementEntry.update_movement_info(dct_m=dct_m)

                loc_string = dct_m['loc_string']
                if loc_string:
                    if len(loc_string.split('.')) > 3:
                        movs = ShiftMovementEntry.changeover_movements(
                            loc_string=loc_string)

                        for m in movs:
                            dct_m = self.dict_all_movements.pop(m, {})
                            if dct_m:
                                dct_m.shift = RECYCLE_BIN_NAME
                                dct_m.shift_id = 2
                                dct_m.update_str_id()

                                ShiftMovementEntry.update_movement_info(
                                    dct_m=dct_m)

        except Exception:
            self.__exception_message = log_exception(
                popup=False, remarks=f'Deleting movement {m} failed!')

    def get_loc_string(self, m):

        return LOC_STRING_SEPERATOR.join(
            [self.dict_all_movements[m]['From'],
             self.dict_all_movements[m]['To'],
             self.dict_all_movements[m]['DepDateTime'].strftime("%H%M")])

    def __refresh_m_leg(self):

        try:
            __set_m = set(
                [m for m in self.dict_all_movements if not self.dict_all_movements[m]['is_repos']])

            # [self.dict_all_movements[m].update_items(
            #     **{'Leg': self.__dct_movement_leg.get(m, '1/1'),
            #        'tu': self.__dct_movement_tu.get(m, 'N/A')}) for m in __set_m]

        except Exception:
            log_exception(popup=False)

    def get_changeover_loc_string(self, cid=0):
        return self.__dct_changeovers.get(cid, {}).get('loc_string', '')

    def get_changeover_id(self, locstring=''):

        if locstring != '':

            idxs = [id for id, dctv in self.__dct_changeovers.items(
            ) if dctv.get('loc_string', '') == locstring]
            if idxs:
                return idxs.pop()

            return 0

        return 0

    def refresh_dct_movement_shift(self, shiftname=''):

        try:
            __set_movs = set(self.dict_all_movements)

            if shiftname != '':
                __shifts = [shiftname]
            else:
                __shifts = list(self.__optimal_drivers)

            for d in __shifts:
                _shift_movs = [m for m in self.__optimal_drivers[d]['list_movements']
                               if m in __set_movs]

                for m in _shift_movs:

                    self.dict_all_movements[m].update_items(
                        **{'shift_id': d,
                           'shift': self.__optimal_drivers[d]['driver'],
                           'draggableX': not self.dict_all_movements[m]['is_repos'],
                           'draggableY': not self.dict_all_movements[m]['is_repos']})

            self.__dct_changeover_shifts = defaultdict(list)
            __set_changeover_movs = set()

            for __id in set(self.__dct_changeovers):

                __kys = set(self.__dct_changeovers[__id])
                __kys = [x for x in __kys if x in range(0, 10)]

                __shifts = []
                for leg in __kys:

                    __m = self.__dct_changeovers[__id][leg]
                    __shifts.append(
                        self.dict_all_movements.get(__m, {}).get('shift', 'N/A'))

                    __set_changeover_movs.update([__m])

                self.__dct_changeover_shifts[__id].extend(__shifts)

            __set_m = set(
                [m for m in self.dict_all_movements if not self.dict_all_movements[m]['is_repos']])

            __set_no_co_m = [
                m for m in __set_m if m not in __set_changeover_movs]

            [self.dict_all_movements[m].update_items(
                **{'loc_string': '.'.join([self.dict_all_movements[m]['From'],
                                           self.dict_all_movements[m]['To'],
                                           self.dict_all_movements[m]['DepDateTime'].strftime("%H%M")])})
             for m in __set_no_co_m]

            for m in __set_m:
                self.dict_all_movements[m].update_items(
                    **{'ChgOverShifts': self.__dct_changeover_shifts.get(
                        self.dict_all_movements[m].get('changeover_id', 0),
                        [self.dict_all_movements[m].get('shift', 'N/A')])})

        except Exception:
            self.__exception_message = log_exception(False)

    def __refresh_dct_max_n_drivers_per_loc(self):

        try:
            if not self.__dct_shift_ids_per_loc_page:
                self.refresh_dct_shift_ids_per_loc_page()

            self.__dct_max_n_drivers_per_loc = {
                dloc: sum(len(self.__dct_shift_ids_per_loc_page[dloc][page])
                          for page in self.__dct_shift_ids_per_loc_page[dloc])
                for dloc in set(self.__dct_shift_ids_per_loc_page)}

        except Exception:
            log_exception(popup=False)

    def refresh_dct_shift_ids_per_loc_page(self):

        try:
            if not self.__optimal_drivers:
                raise ValueError('optimal_drivers is empty!')

            logging.info("Refreshing shift IDs per location page ...")
            self.__dct_drivers = DriversInfo.to_dict()

            __optimal_drivers = secure_copy(self.__optimal_drivers)
            __optimal_drivers.pop(MOVEMENT_DUMP_AREA_NAME, None)
            __optimal_drivers.pop(RECYCLE_BIN_NAME, None)
            self.__dct_shift_ids_per_loc_page = {}
            _dct_shift_idx = {}

            if not UI_PARAMS.SORT_BY_TOUR_LOCSTRING:

                _dct_shift_idx = ShiftIndex.to_dict()
                shift_ids_sorted = []

                if _dct_shift_idx:

                    __shifts_with_no_idx = [
                        x.driver for x in __optimal_drivers.values() if x.driver not in _dct_shift_idx.keys()]

                    if __shifts_with_no_idx:

                        while __shifts_with_no_idx:
                            ShiftIndex.update_shift_index(
                                shiftname=__shifts_with_no_idx.pop())

                        _dct_shift_idx = ShiftIndex.to_dict()

                else:

                    __driver_locs = list(sorted(set([self.__dct_drivers.get(
                        shiftname, {}).get('controlled by', 'N/A') for shiftname in set(__optimal_drivers)])))

                    __driver_locs.remove(
                        'N/A') if 'N/A' in __driver_locs else None

                    __dct_loc_drivers = defaultdict(list)
                    [__dct_loc_drivers[__loc].extend([d for d in set(__optimal_drivers)
                                                      if self.__dct_drivers.get(d, {}).get('controlled by', '') == __loc])
                     for __loc in __driver_locs]

                    for __loc in __driver_locs:

                        tmp_drivers: list = sorted(__dct_loc_drivers[__loc])

                        for shft in tmp_drivers:
                            ShiftIndex.update_shift_index(
                                shiftname=shft, ctrl_loc=__loc)

                    _dct_shift_idx = ShiftIndex.to_dict()
            else:
                sorted_optimal_drivers = dict(
                    sorted(__optimal_drivers.items(), key=lambda x: x[1].tourLocString))
                shift_ids_sorted = list(sorted_optimal_drivers)

        except Exception:
            self.__exception_message = log_exception(False)
            return

        self.__dct_shift_ids_per_loc_page = ShiftIndex.get_dct_shift_ids_per_loc_page(
            pagesize=self.__n_drivers_per_page,
            dct_shift_ids=DriversInfo.to_sub_dict(shift_ids=shift_ids_sorted))

        self.__refresh_dct_max_n_drivers_per_loc()

    def extract_dct_unplanned_movements(self, xlFilepath='',
                                        count_only=False,
                                        get_planned_loc_string=False,
                                        weekdays=[]):


        self.__list_loaded_planned_loc_string = []

        try:
            __set_loaded_planned_movs = set()

            __set_dump_area_movs = set(
                self.__optimal_drivers.get(1, {}).get('list_loaded_movements', []))

            __list_drivers = [d for d in self.__optimal_drivers.keys(
            ) if d not in [1, 2]]

            if weekdays:
                __list_drivers = [d for d in __list_drivers
                                  if DriversInfo.shift_id_runs_on_weekdays(shift_id=d, weekdays=weekdays)]

            while __list_drivers:

                _driver = __list_drivers.pop()
                _loaded_movs = self.__optimal_drivers[_driver].get(
                    'list_loaded_movements', [])
                __set_loaded_planned_movs.update(_loaded_movs)

                if get_planned_loc_string:
                    for m in _loaded_movs:
                        dct_m = self.dict_all_movements.get(m, {})
                        if dct_m:
                            loc_str = '.'.join(
                                [dct_m['From'], dct_m['To'], dct_m['DepDateTime'].strftime('%H%M')])
                            self.__list_loaded_planned_loc_string.append(
                                (loc_str, _driver))

            __set_loaded_movements = set([m for m in set(
                self.dict_all_movements) if self.dict_all_movements[m].is_loaded()])

            __list_unplanned_movements = [
                m for m in __set_loaded_movements if m not in __set_loaded_planned_movs]

            __list_unplanned_movements.extend(list(__set_dump_area_movs))

            set_unplaned_mov = set(__list_unplanned_movements)
            set_all_movements = set(self.dict_all_movements)

            set_unplaned_mov = set(
                [m for m in set_unplaned_mov if m in set_all_movements])

            del __set_loaded_movements, __set_loaded_planned_movs, __set_dump_area_movs

            if count_only:
                return len(set_unplaned_mov)

            self.__dct_unplanned_movements = {}

            if set_unplaned_mov:
                self.__dct_unplanned_movements = {
                    m: self.dict_all_movements[m]
                    for m in set_unplaned_mov}

        except Exception:
            self.__exception_message = log_exception(popup=False,
                                                      remarks='Extracting unplanned movements failed!')
            return {}

        try:

            if self.__dct_unplanned_movements:

                __df_unplanned_movements = DataFrame.from_dict(
                    self.__dct_unplanned_movements, orient='index')

                __df_unplanned_movements[
                    'DrivingTime (hh:mm)'] = __df_unplanned_movements.DrivingTime.apply(
                    lambda x: minutes2hhmm(int(x)))

                __df_unplanned_movements['updated_at'] = datetime.now().strftime(
                    '%Y-%m-%d %H:%M')

                __df_unplanned_movements['DepTime'] = __df_unplanned_movements.DepDateTime.apply(
                    lambda x: x.strftime('%a %H:%M'))

                if xlFilepath != '':
                    xlwriter(df=__df_unplanned_movements.loc[:, [
                        'loc_string', 'From', 'To', 'DepTime', 'TrafficType',
                        'DrivingTime (hh:mm)', 'updated_at']].copy(),
                        sheetname='UnplannedMovements',  xlpath=xlFilepath, keep=True, echo=False)
                else:
                    xlwriter(df=__df_unplanned_movements.loc[:, [
                        'loc_string', 'From', 'To', 'DepTime', 'TrafficType',
                        'DrivingTime (hh:mm)', 'updated_at']].copy(),
                        sheetname='UnplannedMovements',  xlpath=OS_PATH.join(
                        LION_LOGS_PATH, 'unplanned_movements.xlsx'), echo=False)

                del __df_unplanned_movements

        except Exception:
            self.__exception_message = log_exception(
                popup=False, remarks='Dumping unplanned movements failed!')

        if self.__dct_unplanned_movements:
            return self.__dct_unplanned_movements

        return {}

    def get_shifts_in_utilisation_range(self, utilisation_range=[0, 100]):

        try:
            if utilisation_range[0] > 0 or utilisation_range[1] < 100:

                __dct_utilsiation = {d: self.__optimal_drivers[d].get(
                    'time_utilisation', 0) for d in set(self.__optimal_drivers)}

                __list_utilsiation_sorted = sorted(
                    __dct_utilsiation.items(), key=lambda x: x[1])

                __dct_utilsiation = {x[0]: x[1]
                                     for x in __list_utilsiation_sorted}

                __drivers = list(__dct_utilsiation)

                if utilisation_range[0] > 0:
                    for d in __drivers:
                        if __dct_utilsiation[d] < utilisation_range[0]:
                            __dct_utilsiation.pop(d)

                    __drivers = list(__dct_utilsiation)

                if utilisation_range[1] < 100:
                    for d in __drivers:
                        if __dct_utilsiation[d] > utilisation_range[1]:
                            __dct_utilsiation.pop(d)

                    __drivers = list(__dct_utilsiation)

                return __drivers

        except Exception:
            log_exception(
                popup=False, remarks='Could not get get_shifts_in_utilisation_range tours!')

        return []

    def get_infeas_shifts(self):

        try:
            __drivers = list(
                {d: v for d, v in self.__optimal_drivers.items() if not v.get('is_feas', True)})

            return __drivers

        except Exception:
            log_exception(
                popup=False, remarks='Could not get infeasible tours!')

        return []

    def set_axis_ranges(self, **dct_params):

        # dct_params={'hours': 1, 'zoom': 'out', 'page_num': 1}
        __h = int(dct_params['hours'])

        try:
            if dct_params['zoom'] == 'out':

                self.__xAxis_range_start = self.__xAxis_range_start - \
                    timedelta(hours=__h)

                self.__xAxis_range_end = self.__xAxis_range_end + \
                    timedelta(hours=__h)
            else:
                self.__xAxis_range_start = self.__xAxis_range_start + \
                    timedelta(hours=__h)

                self.__xAxis_range_end = self.__xAxis_range_end - \
                    timedelta(hours=__h)

            UserParams.update(xAxis_range_start=self.__xAxis_range_start,
                              xAxis_range_end=self.__xAxis_range_end)

        except Exception:
            self.__exception_message = log_exception(False)

    def update_double_shifts(self, list_db_shifts=[]):

        try:
            self.__dct_drivers = DriversInfo.to_dict()
            __setdrvrs = set(self.__dct_drivers)
            list_db_shifts = [d for d in list_db_shifts if d in __setdrvrs]

            [self.__dct_drivers[d].update({
                'double_man': True
            }) for d in list_db_shifts]

        except Exception:
            self.__exception_message = log_exception(False)

    def update_drivers(self, **dct_params):

        self.__exception_message = ''

        try:

            _shift_id = dct_params['shift_id']
            __driver_name = dct_params['driver_id']
            __operator = dct_params['operator']
            __start_loc = dct_params['start_loc'].split(' - ')[0]
            __ctrl_by = dct_params['ctrl_by'].split(' - ')[0]
            __double_man = dct_params['double_man']
            __vehicle_type = int(dct_params['vehicle_type'])
            __hbr = dct_params['hbr']

            weekdays = dct_params.get('weekdays', [])

            _vehicle = int(self.__optimal_drivers.get(
                _shift_id, {}).get('vehicle', 0))

            _loaded_m = self.__optimal_drivers.get(
                _shift_id, {}).get('list_loaded_movements', [])

            if _loaded_m:

                if _vehicle and _vehicle != __vehicle_type:
                    self.__exception_message = f"{self.__exception_message}Operation not allowed: {
                        __vehicle_type}/{_vehicle}. "

                    return

            __dct_new_driver = {
                'shift_id': _shift_id,
                'controlled by': __ctrl_by,
                'driver id': __driver_name,
                'loc': __start_loc,
                'operator': __operator,
                'start position': __start_loc,
                'double_man': __double_man,
                'vehicle': __vehicle_type,
                'hbr': __hbr,
                'weekdays': weekdays}

            ShiftIndex.update_shift_index(
                shiftname=__driver_name, ctrl_loc=__ctrl_by)

            if _shift_id in self.__optimal_drivers:
                self.__optimal_drivers[_shift_id].update(
                    {'vehicle': __vehicle_type})

                self.__optimal_drivers[_shift_id].shiftname = __driver_name

            DriversInfo.update_drivers_data(**__dct_new_driver)

        except Exception:
            self.__exception_message = f"{
                self.__exception_message}. {log_exception(popup=False)}"

    def clean_up(self):
        """
        Cleans up unused movements as well as empty tours.
        To keep empty shifts on board, please save the schedule as scenario instead of master plan
        """

        try:
            self.__clean_up_empty_shifts()
            self.__clean_up_unused_movements()

        except Exception:
            self.__exception_message = log_exception(False)

    def __sort_list_movements(self, list_of_movs=[]):

        try:
            list_of_movs = [int(m) for m in list_of_movs if int(
                m) in self.dict_all_movements]

            __dct_dt = {
                m: self.dict_all_movements[m]['DepDateTime'] for m in list_of_movs}

            __sorted_dt = dict(
                sorted(__dct_dt.items(), key=lambda item: item[1]))

        except Exception:
            self.__exception_message = log_exception(False)
            return list_of_movs

        return list(__sorted_dt)

    def run_diagnostics(self):

        try:
            self.__find_shifts_with_issues()
            self.__extract_moves_with_mult_shifts()
            self.__get_set_used_movements()

        except Exception:
            log_exception(
                popup=False, remarks='run_diagnostics failed!')

    def calculate_cost(self):

        
        __tcost = TourCost()
        __drivers = set(self.__optimal_drivers)

        while __drivers:

            try:

                driver = __drivers.pop()
                __dct_tour = __tcost.calculate_cost(
                    dct_tour=self.__optimal_drivers.get(driver, {}))

            except Exception:
                log_message(message=f'Tour cost calculation failed for {driver}! {log_exception(False)}',
                           module_name='tour_analysis.py/__calculate_cost_per_supplier')

                __dct_tour = {}

            if __dct_tour:
                self.__optimal_drivers[driver] = __dct_tour

            del __dct_tour

    def __extract_moves_with_mult_shifts(self):

        try:

            __dct_m_with_mult_shift = defaultdict(set)
            for d in self.__optimal_drivers:
                [__dct_m_with_mult_shift[m].update([self.__optimal_drivers[d]['driver']])
                 for m in self.__optimal_drivers[d].list_loaded_movements]

            __m_issues = set([m for m in set(__dct_m_with_mult_shift)
                              if len(__dct_m_with_mult_shift[m]) > 1])

            __dct_m_issues_info = defaultdict(list)

            if __m_issues:

                [__dct_m_issues_info[mm].append(self.dict_all_movements.get(
                    mm, DictMovement(**{})).loc_string) for mm in __m_issues]

                __dct_output = {
                    m: __dct_m_with_mult_shift[m] for m in __m_issues}

                __df_out = DataFrame.from_dict(
                    __dct_output, orient='index')

                __df_out.reset_index(inplace=True)
                __df_out.rename(columns={'index': 'movementid'}, inplace=True)

                csvpath = OS_PATH.join(
                    LION_DIAGNOSTICS_PATH, 'movements with mult shifts.csv')

                __df_out['loc_string'] = __df_out.movementid.apply(
                    lambda x: __dct_m_issues_info.get(x, ''))

                __df_out['shifts'] = __df_out.movementid.apply(
                    lambda m: ';'.join([str(x) for x in __dct_m_with_mult_shift[m]]))

                export_dataframe_as_csv(
                    dataframe=__df_out.loc[:, ['shifts', 'loc_string']].copy(), csv_file_path=csvpath)

        except Exception:
            log_exception(False)

    def __find_shifts_with_issues(self):

        try:
            __str_drivers = ''
            for d in self.__optimal_drivers:

                __movs = self.__optimal_drivers[d]['list_movements']

                __movs = self.__sort_list_movements(list_of_movs=__movs)

                con_ok = True
                if len(__movs) > 1:

                    __m_pairs = [(__movs[i], __movs[i+1])
                                 for i in range(len(__movs)-1)]

                    for pr in __m_pairs:

                        try:

                            __loc1 = self.dict_all_movements.get(
                                pr[0], {}).get('To', '')

                            __loc2 = self.dict_all_movements.get(
                                pr[1], {}).get('From', '')

                            con_ok = con_ok and (__loc1 == __loc2)

                            con_ok = con_ok and (
                                self.dict_all_movements.get(pr[0], {}).get(
                                    'ArrDateTime', None) < self.dict_all_movements[pr[1]]['DepDateTime'])

                            if not con_ok:
                                __str_drivers = '%s%s\n' % (
                                    __str_drivers, self.__optimal_drivers[d]['driver'])
                                break

                        except Exception:
                            pass

        except Exception:
            log_exception(False)

        if __str_drivers != '':

            txtpath = OS_PATH.join(
                LION_DIAGNOSTICS_PATH, 'shifts with issues.txt')

            with open(txtpath, 'w',
                      errors="ignore", encoding="utf8") as __f:
                __f.writelines(__str_drivers)

    @property
    def dct_employed_drivers_per_loc(self):

        try:
            return DriversInfo.get_employed_drivers_per_loc(
                shift_ids=set(self.__optimal_drivers))

        except Exception:
            log_exception(popup=False)
            return {}

UI_SHIFT_DATA = ShiftData.get_instance()
