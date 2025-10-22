from collections import defaultdict
import logging

from lion.runtimes.runtime_mileage_fetcher  import UI_RUNTIMES_MILEAGES
from lion.logger.exception_logger import log_exception
from pandas import DataFrame
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.orm.location import Location
from datetime import datetime, timedelta
from copy import deepcopy
from lion.utils.concat import concat
from lion.bootstrap.constants import MOVEMENT_TYPE_COLOR, INIT_LOADED_MOV_ID
from numpy import inf
from lion.movement.empty_movements import EmptyMovements
from lion.movement.dct_movement import DictMovement
from lion.orm.user_params import UserParams

class MovementManager():

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
            logging.info(f"Initializing UI_MOVEMENTS (MovementManager) ...")
            self.__dct_lane_info = defaultdict(dict)
            self.__dict_movement_color = deepcopy(MOVEMENT_TYPE_COLOR)
            self.__vehicle = 1
            self.__shift = 'N/A'
            self.__shift_id = 0
            self.__list_break_min = [0, 30, 60]
            self.__dict_all_movements = {}
            self.__dct_changeovers = {}
            self.__last_update = int(datetime.now().strftime('%Y%m%d'))

            self.__max_loaded_movement_id = INIT_LOADED_MOV_ID
            self.__df_all_loaded_movements = DataFrame()

            self.__dct_footprint = Location.to_dict()
            self.__reposMovs = EmptyMovements()

            self._initialized = True

        except Exception:
            self._initialized = False
            log_exception(
                popup=True, remarks='Movements could not be initialised')

    def reset(self):
        logging.info("Resetting MovementManager instance...")
        self._initialized = False
        self.initialize()

    @classmethod
    def get_instance(cls):
        return cls()

    @property
    def vehicle(self):
        return self.__vehicle

    @vehicle.setter
    def vehicle(self, x):
        self.__vehicle = x
        self.__reposMovs.vehicle = x

    @property
    def shift(self):
        return self.__shift

    @shift.setter
    def shift(self, x):
        self.__shift = x
        self.__reposMovs.shift = x

    @property
    def shift_id(self):
        return self.__shift_id

    @shift_id.setter
    def shift_id(self, x):
        self.__shift_id = x
        self.__reposMovs.shift_id = x

    @property
    def dct_changeovers(self):
        return self.__dct_changeovers

    @dct_changeovers.setter
    def dct_changeovers(self, x):
        self.__dct_changeovers = x

    @property
    def list_break_min(self):
        return self.__list_break_min

    @list_break_min.setter
    def list_break_min(self, x):
        self.__list_break_min = x
        self.__reposMovs.list_break_min = x

    @property
    def dict_all_movements(self):
        return self.__dict_all_movements

    @dict_all_movements.setter
    def dict_all_movements(self, dct_all_movements={}):

        if len(dct_all_movements) == 0:
            logging.critical(f"Clearing up dict_all_movements: {len(dct_all_movements)} movements ...")

        self.__dict_all_movements = dct_all_movements
        self._clean_up_cages_ulds()
        self.__refresh_df_all_loaded_movements()

    @property
    def set_all_movements(self):
        return set(self.__dict_all_movements)

    def _clean_up_cages_ulds(self):

        try:
            __m_list = [m for m in set(self.__dict_all_movements) if self.__dict_all_movements.get(m, {}).get(
                'TrafficType', '').lower() in ['cages', 'uld', 'ulds', "uld's"]]

            if __m_list:

                for m in __m_list:

                    __type = self.__dict_all_movements.get(
                        m, {}).get('TrafficType', '')
                    self.dict_all_mov__dict_all_movementsements[m].update_items(
                        **{'TrafficType': 'Empty - %s' % __type})

                [self.__dict_all_movements[m].update_items(
                    **{'TrafficType': 'Express - Scottish'}) for m in __m_list]

        except Exception:
            log_exception(
                popup=False, remarks='dict_all_movements could not be cleaned up cages/ULDs!')

    def refresh_movement_id(self):
        """
        Refreshes the maximum loaded movement ID and updates the minimum empty movement ID provided by the user.
        This method retrieves the current maximum movement IDs from the local movements and updates the internal
        state accordingly. If an error occurs during the process, it logs the exception without raising a popup.
        Raises:
            Logs any exception encountered during the refresh process.
        """

        try:
            _max_loaded_id, _max_repos_id = ShiftMovementEntry.get_max_movement_ids()
            self.__max_loaded_movement_id = max(_max_loaded_id, self.__max_loaded_movement_id)
            self.__reposMovs.refresh_min_empty_movement_id(new_empty_movement_id=_max_repos_id)

            del _max_loaded_id, _max_repos_id
        except Exception:
            log_exception(
                popup=False, remarks='max_loaded_movement_id was not refreshed!')

    def get_new_loaded_movement_id(self):
        try:
            self.__max_loaded_movement_id += 1
            return self.__max_loaded_movement_id
        except Exception:
            log_exception(
                popup=True, remarks='max_loaded_movement_id was not refreshed!')

    def __refresh_df_all_loaded_movements(self):

        try:
            if self.__dict_all_movements:

                self.__df_all_loaded_movements = DataFrame.from_dict(
                    {k: v for k, v in self.__dict_all_movements.items() 
                     if v['TrafficType'].lower() != 'empty'}, orient='index')

                self.__max_loaded_movement_id = max(self.__max_loaded_movement_id, max(
                    self.__df_all_loaded_movements.MovementID.tolist())) + 1

                self.__reposMovs.max_repos_movement_id = max(
                    list(self.__dict_all_movements)) + 1

        except Exception:
            log_exception(
                popup=False, remarks='Refreshing df_all_loaded_movements failed!')

    def __categorize_repos_driving_time(self, dt):
        __list = [60, 90, 120, 150, 180, 270, 10000]

        while __list:
            __cat = __list.pop(0)
            if dt <= __cat:
                return __cat

    def _get_runtimes_info(self, orig, dest, vehicle):

        try:
            runtime, dist = UI_RUNTIMES_MILEAGES.retrieve_travel_time_and_distance(
                orig=orig, dest=dest, vehicle=vehicle)

            if runtime and dist:
                dct_data = {'dist': dist, 'runtime': runtime}
                self.__dct_lane_info['|'.join(
                    [orig, dest, str(vehicle)])].update(dct_data)

                return dct_data

        except Exception:
            log_exception(popup=False, 
                          remarks=f"No data runtimes data found for {'|'.join([orig, dest, str(vehicle)])}")
            return None


    def get_dct_arriving_movement(self, orig,
                                  dest, ArrDateTime,
                                  vehicle=None, shift=None, shift_id=0):

        try:

            if vehicle is None:
                vehicle = self.__vehicle

            if shift is None:
                shift = self.__shift

            if not shift_id:
                shift_id = self.__shift_id

            dct_runtimes_data = self.__dct_lane_info.get('|'.join([orig, dest, str(vehicle)]),
                                                         self._get_runtimes_info(orig=orig, dest=dest, vehicle=vehicle))

            if not dct_runtimes_data:
                return None

            __DrivingTime_utc = dct_runtimes_data['runtime']

            if not __DrivingTime_utc or __DrivingTime_utc >= inf:
                return None

            DepDateTime = ArrDateTime - timedelta(minutes=__DrivingTime_utc)
            del __DrivingTime_utc

            self.__update_repos_movement_id()

            dct_m = {}

            dct_m['DrivingTime'] = dct_runtimes_data['runtime']
            dct_m['Dist'] = dct_runtimes_data['dist']
            dct_m['MovementID'] = self.__new_repos_movement_id
            dct_m['From'] = orig
            dct_m['To'] = dest
            dct_m['VehicleType'] = vehicle
            dct_m['ArrDateTime'] = ArrDateTime
            dct_m['DepDateTime'] = DepDateTime
            dct_m['tu'] = ''
            dct_m['shift'] = shift
            dct_m['shift_id'] = shift_id

            dct_m['loc_string'] = ''

            dct_m['Utilisation'] = 0
            dct_m['PayWeight'] = 0
            dct_m['Capacity'] = 0
            dct_m['is_repos'] = True
            dct_m['TrafficType'] = 'Empty'
            dct_m['draggableX'] = False
            dct_m['draggableY'] = False

            dct_m['n_drivers'] = 1

            dct_m['weighted_dist'] = dct_m['Dist']
            dct_m['CountryFrom'] = self.__dct_footprint[dct_m['From']]['country_code']

            dct_m = DictMovement(**dct_m)

            # These movements are empty, thus leg is always 1 as they are not part of any changeover in theory
            dct_m['leg'] = 1
            dct_m['legs'] = 1

            self.__dict_all_movements.update(
                {self.__new_repos_movement_id: dct_m})

            return dct_m  # dct_nested_idle

        except Exception:
            log_exception(
                popup=False, remarks=f"Arriving movement from {orig} -> {dest} failed!")
            return None

    def get_dct_departing_movement(self, orig, dest, DepDateTime, vehicle=None, shift=None, shift_id=0):

        dct_m = {}

        try:

            if Location.is_customer(orig):
                return {}
            
            self.__update_repos_movement_id()

            if vehicle is None:
                vehicle = self.__vehicle

            if not shift_id:
                shift_id = self.__shift_id

            if shift is None:
                shift = self.__shift

            dct_runtimes_data = self.__dct_lane_info.get('|'.join([orig, dest, str(vehicle)]),
                                                         self._get_runtimes_info(orig=orig, dest=dest, vehicle=vehicle))

            if not dct_runtimes_data:
                return None

            __driving_time = dct_runtimes_data['runtime']

            if not __driving_time or __driving_time >= inf:
                return None

            dct_m['MovementID'] = self.__new_repos_movement_id
            dct_m['From'] = orig
            dct_m['To'] = dest
            dct_m['VehicleType'] = vehicle
            dct_m['tu'] = ''
            dct_m['shift'] = shift
            dct_m['shift_id'] = shift_id

            dct_m['DepDateTime'] = DepDateTime
            dct_m['DrivingTime'] = __driving_time

            dct_m['ArrDateTime'] = dct_m['DepDateTime'] + timedelta(
                minutes=dct_runtimes_data['runtime'])

            dct_m['loc_string'] = ''

            dct_m['Utilisation'] = 0
            dct_m['PayWeight'] = 0
            dct_m['Capacity'] = 0
            dct_m['is_repos'] = True
            dct_m['TrafficType'] = 'Empty'
            dct_m['draggableX'] = False
            dct_m['draggableY'] = False
            dct_m['n_drivers'] = 1

            if not dct_runtimes_data['dist']:
                raise ValueError(
                    'No mileage was found for %s->%s.' % (orig, dest))

            dct_m['Dist'] = dct_runtimes_data['dist']

            dct_m['CountryFrom'] = self.__dct_footprint[dct_m['From']]['country_code']

            dct_m = DictMovement(**dct_m)

            # These movements are empty, thus leg is always 1 as they are not part of any changeover in theory
            dct_m['leg'] = 1
            dct_m['legs'] = 1

            self.__dict_all_movements.update(
                {self.__new_repos_movement_id: dct_m})

            return dct_m

        except Exception:
            log_exception(
                popup=False, remarks=f"Departing movement from {orig} -> {dest} failed")
            return None

    def get_dct_adhoc_movement(self,
                               orig,
                               dest,
                               traffic_type,
                               tu_loc,
                               loc_string,
                               DepDateTime,
                               ArrDateTime,
                               vehicle=None,
                               shift=None,
                               shift_id=0):

        try:

            if vehicle is None:
                vehicle = self.__vehicle

            if shift is None:
                shift = self.__shift

            if not shift_id:
                shift_id = self.__shift_id

            dct_m = {}
            _is_repos = traffic_type.lower() == 'empty'
            loc_string = loc_string if len(loc_string.split('.')) > 3 else ''

            dct_runtimes_data = self.__dct_lane_info.get('|'.join([orig, dest, str(vehicle)]),
                                                         self._get_runtimes_info(orig=orig, dest=dest, vehicle=vehicle))

            __driving_time = dct_runtimes_data['runtime']

            if not __driving_time or __driving_time >= inf:
                raise Exception(
                    f'No runtimes was found between {orig} and {dest}! Check if locations exist or runtimes data is up-to-date!')

            dct_m['From'] = orig
            dct_m['To'] = dest
            dct_m['VehicleType'] = vehicle
            dct_m['TrafficType'] = traffic_type
            dct_m['tu'] = tu_loc
            dct_m['loc_string'] = loc_string

            # '%s.%s.%s' % (
            #     orig, dest, DepDateTime.strftime("%H%M"))

            dct_m['draggableX'] = True
            dct_m['draggableY'] = False if _is_repos else True
            # dct_m['color_category'] = 'repos' if _is_repos else 'input'
            dct_m['is_repos'] = _is_repos
            dct_m['shift'] = shift
            dct_m['shift_id'] = shift_id

            # dct_m['linehaul_id'] = '.'.join(
            #     [orig, dest, DepDateTime.strftime("%H%M")])

            dct_m['DepDateTime'] = DepDateTime
            dct_m['DrivingTime'] = __driving_time

            if DepDateTime is None:
                dct_m['DepDateTime'] = dct_m['ArrDateTime'] - timedelta(
                    minutes=__driving_time)
            else:
                dct_m['DepDateTime'] = DepDateTime

            if ArrDateTime is None:
                dct_m['ArrDateTime'] = dct_m['DepDateTime'] + timedelta(
                    minutes=__driving_time)
            else:
                dct_m['ArrDateTime'] = ArrDateTime


            dct_m['Utilisation'] = 0.01
            dct_m['PayWeight'] = 0
            dct_m['Capacity'] = 0

            dct_m['n_drivers'] = 1

            dct_m['Dist'] = dct_runtimes_data['dist']
            dct_m['CountryFrom'] = self.__dct_footprint[dct_m['From']
                                                        ]['country_code']

            __df_adhoc_movement = DataFrame([dct_m])

            __df_adhoc_movement[
                'driving_time_category'] = __df_adhoc_movement.DrivingTime.apply(
                lambda x: int(self.__categorize_repos_driving_time(x))
            )

            __df_adhoc_movement['is_repos'] = __df_adhoc_movement.is_repos.astype(
                bool)
            __df_adhoc_movement['draggableY'] = __df_adhoc_movement.draggableY.astype(
                bool)
            __df_adhoc_movement['draggableX'] = __df_adhoc_movement.draggableX.astype(
                bool)

            self.__df_all_loaded_movements = concat(
                [self.__df_all_loaded_movements, __df_adhoc_movement])

            dct_m = DictMovement(**dct_m)

        except Exception:
            log_exception(
                popup=False, remarks=f"adhoc movement from {orig} -> {dest} failed")

            return None
        
        movement_id = ShiftMovementEntry.add_dct_m(dct_m)
        if not movement_id:
            return None
        
        try:
            dct_m['MovementID'] = movement_id
            self.__max_loaded_movement_id = movement_id
            self.__dict_all_movements.update({movement_id: dct_m})

            return dct_m

        except Exception:
            logging.critical("Updating dict_all_movements with new movement failed!")
            return None


    def get_all_df_movements(self,
                             set_input_movements=set(),
                             maxreposmin=0):
        """
        Returns all loaded and repos movements based on the provided set_input_movements.
        """
        try:

            if self.__df_all_loaded_movements.empty:
                self.__refresh_df_all_loaded_movements()

            if not set_input_movements:
                if not maxreposmin:
                    return self.__df_all_loaded_movements

                set_input_movements = set(
                    self.__df_all_loaded_movements.MovementID.tolist())

            __df_movements = self.__df_all_loaded_movements[
                self.__df_all_loaded_movements.MovementID.isin(set_input_movements)].copy()

            if not maxreposmin:
                return __df_movements

            self.__reposMovs.df_movements = __df_movements
            self.__reposMovs.vehicle = self.__vehicle
            self.__reposMovs.shift = self.__shift

            __df_repos = self.__reposMovs.df_repos_movements

            __df_repos = __df_repos[__df_repos.DrivingTime <= maxreposmin].copy()

            self.__update_dict_all_movements(df_movements=__df_repos)

            __df_repos['is_repos'] = __df_repos.is_repos.astype(bool)
            __df_repos['is_adhoc'] = __df_repos.is_adhoc.astype(bool)
            __df_repos['draggableY'] = __df_repos.draggableY.astype(
                bool)
            __df_repos['draggableX'] = __df_repos.draggableX.astype(
                bool)

        except Exception:
            __df_repos = DataFrame()
            __df_movements = DataFrame()
            log_exception(popup=False)

        if not __df_repos.empty:
            __df_movements = concat(
                [__df_movements, __df_repos])

        return __df_movements

    def __update_repos_movement_id(self):
        self.__new_repos_movement_id = self.__reposMovs.update_repos_movement_id()

    def __update_dict_all_movements(self, df_movements=DataFrame()):

        try:
            df_movements['IDX'] = df_movements.MovementID.tolist()
            df_movements.set_index(['IDX'], inplace=True)
            __dct_movements: dict = df_movements.to_dict(orient='index')

            self.__dict_all_movements.update(
                {m: DictMovement(**v) for m, v in __dct_movements.items()})

        except Exception:
            log_exception(
                popup=True, remarks='__update_dict_all_movements failed!')

    def update_movement_for_new_deptime(self, m, new_dep_dt):

        __dct_m = self.__dict_all_movements.get(m, {})
        __dct_m_backup = self.__dict_all_movements.get(m, {})

        try:
            __dct_m.dep_date_time = new_dep_dt
        except Exception:
            try:
                __dct_m = DictMovement(**__dct_m)
                __dct_m.weekday = UserParams.get_param(
                    param='active_weekday', if_null='Mon')
                __dct_m.dep_date_time = new_dep_dt

            except Exception:
                log_exception(popup=False, remarks=f"Time change failed!")
                __dct_m = __dct_m_backup

        if __dct_m:
            self.__dict_all_movements.update({m: __dct_m})

        del __dct_m_backup, __dct_m

    def get_turnaroundtime(self, loc):

        try:
            __turnaround_drive = self.__dct_footprint[loc]['chgover_driving_min']
            __turnaround_non_drive = self.__dct_footprint[loc]['chgover_non_driving_min']

            return __turnaround_drive + __turnaround_non_drive

        except Exception:
            log_exception(popup=False, remarks='get_turnaroundtime failed!')
            return None

    def insert_intermediate_m(self, m1, m2, idle_time=0, vehicle=None, shift=None, shift_id=0):

        try:

            if Location.is_customer(self.__dict_all_movements[m1]['To']):
                return None

            if vehicle is None:
                vehicle = self.__vehicle

            if shift is None:
                shift = self.__shift

            if not shift_id:
                shift_id = self.__shift_id

            __turnaroundtime = self.get_turnaroundtime(
                self.__dict_all_movements[m1]['To'])

            __dct_m = self.get_dct_adhoc_repos_movement(
                orig=self.__dict_all_movements[m1]['To'],
                dest=self.__dict_all_movements[m2]['From'],
                DepDateTime=self.__dict_all_movements[m1]['ArrDateTime'] + timedelta(
                    minutes=__turnaroundtime + idle_time
                ),
                vehicle=vehicle,
                shift=shift,
                shift_id=shift_id
            )

            __delta = int(
                0.5 + (self.__dict_all_movements[m2]['DepDateTime'] - __dct_m['ArrDateTime']).total_seconds()/60)

            if __delta < self.get_turnaroundtime(__dct_m['To']):
                # change departure time of m2
                self.update_movement_for_new_deptime(m2, __dct_m['ArrDateTime'] + timedelta(
                    minutes=self.get_turnaroundtime(__dct_m['To'])))

            return __dct_m['MovementID']

        except Exception:
            log_exception(
                popup=False, remarks='insert_intermediate_m failed!')

            return None

    def get_dct_adhoc_repos_movement(self,
                                     orig,
                                     dest,
                                     DepDateTime,
                                     vehicle=None,
                                     shift=None,
                                     shift_id=0):

        if vehicle is None:
            vehicle = self.__vehicle

        if shift is None:
            shift = self.__shift

        if not shift_id:
            shift_id = self.__shift_id

        dct_runtimes_data = self.__dct_lane_info.get('|'.join([orig, dest, str(vehicle)]),
                                                     self._get_runtimes_info(orig=orig, dest=dest, vehicle=vehicle))

        __DrivingTime_utc = dct_runtimes_data['runtime']

        if __DrivingTime_utc >= inf:
            return None

        ArrDateTime = DepDateTime + timedelta(minutes=__DrivingTime_utc)
        del __DrivingTime_utc

        dct_m = {}

        self.__update_repos_movement_id()

        try:

            dct_m['MovementID'] = self.__new_repos_movement_id
            dct_m['From'] = orig
            dct_m['To'] = dest
            dct_m['VehicleType'] = vehicle
            dct_m['ArrDateTime'] = ArrDateTime
            dct_m['DepDateTime'] = DepDateTime
            dct_m['tu'] = ''
            dct_m['shift'] = shift
            dct_m['shift_id'] = shift_id

            dct_m['loc_string'] = ''

            if not dct_runtimes_data['runtime']:
                raise ValueError(f"Invalid runtime: {
                                 dct_runtimes_data['runtime']}")

            dct_m['DrivingTime'] = dct_runtimes_data['runtime']
            dct_m['Utilisation'] = 0
            dct_m['PayWeight'] = 0
            dct_m['Capacity'] = 0
            dct_m['color'] = self.__dict_movement_color['repos']
            dct_m['is_repos'] = True
            # dct_m['is_adhoc'] = False
            dct_m['TrafficType'] = 'Empty'
            # dct_m['color_category'] = 'repos'
            dct_m['draggableX'] = False
            dct_m['draggableY'] = False

            dct_m['n_drivers'] = 1

            dct_m['Dist'] = dct_runtimes_data['dist']

            dct_m['CountryFrom'] = self.__dct_footprint[dct_m['From']]['country_code']

            dct_m = DictMovement(**dct_m)

            self.__dict_all_movements.update(
                {self.__new_repos_movement_id: dct_m})

            return dct_m

        except Exception:
            log_exception(
                popup=False,
                remarks=f'get_dct_adhoc_repos_movement from {orig} to {dest} failed!')

            return {}

    @ property
    def dict_all_movements_recalc(self):
        """
        This version returns recalculated data but does not change attribute self.__dict_all_movements
        """

        __dict_all_movements_recalc = deepcopy(self.__dict_all_movements)
        for m in self.__dict_all_movements:
            try:
                dct_m = self.__dict_all_movements[m]

                dct_runtimes_data = self.__dct_lane_info.get('|'.join([dct_m['From'], dct_m['To'], str(dct_m['VehicleType'])]),
                                                             self._get_runtimes_info(orig=dct_m['From'], dest=dct_m['To'], vehicle=dct_m['VehicleType']))

                __driving_time = dct_runtimes_data['runtime']

                __dict_all_movements_recalc[m].update(
                    {'DrivingTime': __driving_time,
                     'ArrDateTime': dct_m['DepDateTime'] + timedelta(minutes=__driving_time)})

            except Exception:
                log_exception(
                    popup=False, remarks='movement could not be recalculated!')
                pass

        return __dict_all_movements_recalc

    def rebuild_movement(self,
                         m,
                         orig,
                         dest,
                         traffic_type,
                         tu_loc,
                         loc_string,
                         DepDateTime=None,
                         ArrDateTime=None,
                         vehicle=None,
                         shift=None,
                         shift_id=0):

        try:

            dct_m = {}

            if shift is None:
                shift = self.__shift

            if not shift_id:
                shift = self.__shift_id

            if DepDateTime is None and ArrDateTime is None:
                raise ValueError('Please specify DepDateTime or ArrDateTime!')

            if vehicle is None:
                vehicle = self.__vehicle

            dct_runtimes_data = self.__dct_lane_info.get('|'.join([orig, dest, str(vehicle)]),
                                                         self._get_runtimes_info(orig=orig, dest=dest, vehicle=vehicle))

            __driving_time = dct_runtimes_data['runtime']

            if __driving_time is None:
                raise ValueError('Driving time was None!')

            _is_repos = traffic_type.lower() == 'empty'

            if DepDateTime is None:

                dct_m['ArrDateTime'] = ArrDateTime
                dct_m['DepDateTime'] = ArrDateTime - timedelta(
                    minutes=__driving_time)

            elif ArrDateTime is None:

                dct_m['DepDateTime'] = DepDateTime
                dct_m['ArrDateTime'] = DepDateTime + timedelta(
                    minutes=__driving_time)

            dct_m['MovementID'] = int(m)
            dct_m['From'] = orig
            dct_m['To'] = dest
            dct_m['VehicleType'] = vehicle
            dct_m['TrafficType'] = traffic_type
            dct_m['tu'] = tu_loc
            dct_m['loc_string'] = loc_string if loc_string != '' else ''
            # '%s.%s.%s' % (
            #     orig, dest, dct_m['DepDateTime'].strftime("%H%M"))

            dct_m['shift'] = shift
            dct_m['shift_id'] = shift_id

            dct_m['draggableX'] = True
            dct_m['draggableY'] = False if _is_repos else True
            dct_m['is_repos'] = _is_repos

            dct_m['DrivingTime'] = __driving_time

            dct_m['Utilisation'] = 0.01
            dct_m['PayWeight'] = 0
            dct_m['Pieces'] = 0
            dct_m['Capacity'] = 18000
            dct_m['n_drivers'] = 1

            dct_m['Dist'] = dct_runtimes_data['dist']
            dct_m['CountryFrom'] = self.__dct_footprint[dct_m['From']
                                                        ]['country_code']

            dct_m['last_update'] = self.__last_update
            dct_m['leg'] = 1

            dct_m = DictMovement(**dct_m)
            dct_m.update_str_id()

            return dct_m

        except Exception:
            log_exception(
                popup=False, remarks=f'Error when building {orig}->{dest}: {vehicle} movement!')
            return DictMovement({})

UI_MOVEMENTS = MovementManager.get_instance()

# def recal_dist_runtimes(self):

#         try:
#             update_log(
#                 message=f'Recalculating {len(self.__dict_all_movements)} movements.')

#             set_movs = set(self.__dict_all_movements)
#             self.__dct_lane_info = defaultdict(dict)

#             for m in set(self.__dict_all_movements):
#                 self.__dict_all_movements[m].create_linehaul_id()

#             __dct_backup = deepcopy(self.__dict_all_movements)

#             __df1 = DataFrame.from_dict(
#                 self.__dict_all_movements, orient='index').loc[:, [
#                     'MovementID', 'linehaul_id', 'DrivingTime', 'Dist', 'ArrDateTime']].copy()

#             __df1['Miles'] = __df1.Dist.apply(lambda x: km2mile(x))
#             __df1['ArrDateTime'] = __df1.ArrDateTime.apply(
#                 lambda x: x.strftime('%a %H:%M'))

#             __df1.rename(columns={
#                         c: f'{c}_1' for c in ['linehaul_id', 'DrivingTime', 'Miles', 'ArrDateTime']}, inplace=True)

#             while set_movs:

#                 m = set_movs.pop()
#                 orig = self.__dict_all_movements[m]['From']
#                 dest = self.__dict_all_movements[m]['To']
#                 vehicle = self.__dict_all_movements[m]['VehicleType']

#                 dct_data = self.__dct_lane_info.get('|'.join([orig, dest, str(vehicle)]),
#                                                     self._get_runtimes_info(orig=orig, dest=dest, vehicle=vehicle))

#                 if dct_data:
#                     self.__dict_all_movements[m].update({'Dist': dct_data['dist'],
#                                                         'DrivingTime': dct_data['runtime']})

#         except Exception:
#             log_exception(
#                 popup=True, remarks='Recalculating recal_dist_runtimes failed!')
#             self.__dict_all_movements = deepcopy(__dct_backup)

#             return

#         try:

#             __df2 = DataFrame.from_dict(
#                 self.__dict_all_movements, orient='index').loc[:, [
#                     'MovementID', 'linehaul_id', 'DrivingTime', 'Dist', 'ArrDateTime']].copy()

#             __df2['Miles'] = __df2.Dist.apply(lambda x: km2mile(x))
#             __df2['ArrDateTime'] = __df2.ArrDateTime.apply(
#                 lambda x: x.strftime('%a %H:%M'))

#             __df2.rename(
#                 columns={c: f'{c}_2' for c in ['linehaul_id', 'DrivingTime', 'Miles', 'ArrDateTime']}, inplace=True)

#             __df2 = __df2.merge(__df1, on=['MovementID'], how='inner').copy()

#             __df2['Diff'] = __df2.apply(lambda x: (x['DrivingTime_1'] != x['DrivingTime_2']) or (
#                 x['Miles_1'] != x['Miles_2']) or (x['ArrDateTime_1'] != x['ArrDateTime_2']), axis=1)

#             __df2 = __df2[__df2.Diff].copy().loc[:, ['linehaul_id_1',
#                                                      'DrivingTime_1', 'DrivingTime_2',
#                                                      'Miles_1', 'Miles_2', 'ArrDateTime_1',
#                                                      'ArrDateTime_2']].copy()

#             xlwriter(df=__df2, sheetname='Movements',  xlpath=OS_PATH.join(
#                 LION_OPTIMIZATION_PATH, 'runtimes_scn_impacted_movements.xlsx'), echo=False)

#         except Exception:
#             log_exception(
#                 popup=False, remarks='Calculating runtimes_scn_impacted_movements failed!')

#         self.__refresh_df_all_loaded_movements()
#         del __dct_backup, set_movs