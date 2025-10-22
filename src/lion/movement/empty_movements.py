from collections import defaultdict
from datetime import timedelta
from os import getenv
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.ui.ui_params import UI_PARAMS
from lion.logger.exception_logger import log_exception
from lion.orm.user_params import UserParams
from lion.utils.concat import concat
from pandas import DataFrame
from numpy import inf
from lion.bootstrap.constants import MOVEMENT_TYPE_COLOR, MIN_REPOS_MOVEMENT_ID
import lion.utils.dfgroupby as dfgroupby
from lion.orm.location import Location


class EmptyMovements():

    def __init__(self):

        try:

            self.__df_movements = DataFrame()
            self.__df_repos_movements = DataFrame()

            self.__weighted_dist_val = 1

            self.__max_repos_driving_time = UserParams.get_param('maxreposdrivmin', 270)

            self.__dct_footprint = Location.to_dict()
            self.__set_non_customers = set([x for x, v in self.__dct_footprint.items() 
                                            if v['loc_type'].lower() != 'customer'])

            self.__list_break_min = [0, 60]

            self.__vehicle = 1
            self.__shift = 'N/A'
            self.__shift_id = 0
            self.__max_repos_movement_id = MIN_REPOS_MOVEMENT_ID * 1
            self.__dct_lane_info = defaultdict(dict)

        except Exception:
            log_exception(
                popup=True, remarks='EmptyMovements could not be initialised!')

    def refresh_min_empty_movement_id(self, new_empty_movement_id=None):
        if new_empty_movement_id is None:
            new_empty_movement_id = MIN_REPOS_MOVEMENT_ID * 1
        self.__max_repos_movement_id = max(new_empty_movement_id, self.__max_repos_movement_id)

    @property
    def shift(self):
        return self.__shift

    @shift.setter
    def shift(self, x):
        self.__shift = x

    @property
    def shift_id(self):
        return self.__shift_id

    @shift_id.setter
    def shift_id(self, x):
        self.__shift_id = x

    @property
    def vehicle(self):
        return self.__vehicle

    @vehicle.setter
    def vehicle(self, x):
        self.__vehicle = x

    @property
    def list_break_min(self):
        return self.__list_break_min

    @list_break_min.setter
    def list_break_min(self, x):
        self.__list_break_min = x

    @property
    def max_repos_movement_id(self):
        return self.__max_repos_movement_id

    @max_repos_movement_id.setter
    def max_repos_movement_id(self, x):
        self.__max_repos_movement_id = max([x, self.__max_repos_movement_id])

    @property
    def df_movements(self):
        return self.__df_movements

    @df_movements.setter
    def df_movements(self, df_movements):
        self.__df_movements = df_movements
        self.__generate_repos_movements()

    @property
    def df_repos_movements(self):
        return self.__df_repos_movements

    @property
    def dct_loc_repos_movement_ids(self):
        return self.__dct_loc_repos_movement_ids

    def __generate_repos_movements(self):

        self.__list_break_min = UI_PARAMS.LIST_BREAK_MIN
        self.__max_repos_driving_time = UI_PARAMS.MAX_REPOS_DRIV_MIN

        setLocsFrom = set()
        self.__set_locs_to = set()
        ToLocs = set()

        self.__df_repos_movements = DataFrame(columns=[
            'MovementID',
            'linehaul_id',
            'From',
            'To',
            'loc_string',
            'VehicleType',
            'DepDateTime',
            'ArrDateTime',
            'DrivingTime',
            'tu',
            'Dist',
            'Capacity',
            'PayWeight',
            'Utilisation',
            'is_repos',
            'is_adhoc',
            'weighted_dist',
            'n_drivers',
            'category',
            'color_category',
            'draggableX',
            'draggableY',
            'shift',
            'shift_id']
        )

        self.__df_repos_movements_empty = self.__df_repos_movements.copy()

        try:

            self.__df_od_combinations = dfgroupby.groupby(df=self.__df_movements[
                self.__df_movements.To.isin(self.__set_non_customers)].copy(),
                                                          groupby_cols=[
                                                              'From', 'To', 'ArrDateTime'],
                                                          agg_cols_dict={'Dist': 'max'})
            if self.__df_od_combinations.empty:
                return
            
            setLocsFrom = set(self.__df_od_combinations.To.tolist())
            self.__set_locs_to = set(self.__df_od_combinations.From.tolist())

            self.__dct_dist = {(x1, x2): float(0 if x1 == x2 else self.__get_movement_dist(
                orig=x1, dest=x2, vehicle=self.__vehicle, if_none=inf))
                for x1 in setLocsFrom for x2 in self.__set_locs_to}


            if not self.__dct_dist:
                return

            self.__df_repos_movements[
                'is_repos'] = self.__df_repos_movements.is_repos.astype(bool)
            self.__df_repos_movements[
                'is_adhoc'] = self.__df_repos_movements.is_adhoc.astype(bool)
            self.__df_repos_movements[
                'draggableY'] = self.__df_repos_movements.draggableY.astype(bool)
            self.__df_repos_movements[
                'draggableX'] = self.__df_repos_movements.draggableX.astype(bool)

            ToLocs = set([x[0] for x in self.__dct_dist.keys()])

        except Exception:
            log_exception(
                popup=False, remarks='Initializing repositioning movements failed.')

            return

        try:

            
            while ToLocs:
                self.__create_repos_per_loc(ToLocs.pop())

            __df_repos_movements = dfgroupby.groupby(
                df=self.__df_repos_movements,
                groupby_cols=[
                    'From', 'To', 'MovementID', 'category']).copy()

            self.__dct_loc_repos_movement_ids = __df_repos_movements.groupby('From', group_keys=True).apply(
                lambda x: x.groupby('To', group_keys=True).apply(lambda y: y.groupby('category', group_keys=True)[
                    'MovementID'].apply(list).to_dict()).to_dict()).to_dict()

            self.__df_repos_movements.drop(['category'], axis=1, inplace=True)

            self.__df_repos_movements['color'] = MOVEMENT_TYPE_COLOR['repos']
            self.__df_repos_movements['CountryFrom'] = self.__df_repos_movements.From.apply(
                lambda x: self.__dct_footprint.get(
                    x, {}).get('country_code', ''))

            self.__df_repos_movements['FixedDriver'] = ''
            self.__df_repos_movements['TrafficType'] = 'Empty'

        except Exception:
            self.__df_repos_movements = self.__df_repos_movements_empty.copy()
            log_exception(
                popup=True, remarks='Building repositioning movements failed.')

            return

        return

    def __create_repos_per_loc(self, loc):

        try:
            __df_movements = self.__df_od_combinations[
                self.__df_od_combinations.To == loc].copy()

            if __df_movements.empty:
                return

            __df_movements.reset_index(inplace=True)
            __df_movements.drop('index', inplace=True, axis=1)

            _turnaround_time = self.__dct_footprint.get(
                loc, {}).get('turnaround_min', 25)

            df_repos_movs = dfgroupby.groupby(df=__df_movements,
                                              groupby_cols=[
                                                  'To', 'ArrDateTime'],
                                              agg_cols_dict={'Dist': 'max'})

            __df = DataFrame(
                columns=['To', 'ArrDateTime', 'DepDateTime', 'MovementID', 'category'])

            # Generate repositioning movement departing per time slot
            for mints in self.__list_break_min:

                __df0 = df_repos_movs.copy()

                __df0['DepDateTime'] = __df0.ArrDateTime.apply(
                    lambda x: x + timedelta(minutes=mints + _turnaround_time))

                __df0['category'] = mints

                __df = concat(
                    [__df, __df0])

            df_repos_movs = __df.copy()
            del __df

            df_repos_movs.rename(
                columns=({'ArrDateTime': 'mov_ArrDateTime'}), inplace=True)

            df_repos_movs['tmpID'] = 'Temp_ID'

            locs = set([x for x in self.__set_locs_to if (
                loc, x) in self.__dct_dist.keys() and x != loc])

            if locs != []:

                df_loc_to = DataFrame(list(locs), columns=['LocTo'])
                df_loc_to['tmpID'] = 'Temp_ID'

                df_repos_movs = df_repos_movs.merge(
                    df_loc_to, on=['tmpID'])

                df_repos_movs.rename(columns={'To': 'From', 'LocTo': 'To'},
                                     inplace=True)

                df_repos_movs['VehicleType'] = self.__vehicle
                df_repos_movs['shift'] = self.__shift
                df_repos_movs['shift_id'] = self.__shift_id

                df_repos_movs['Dist'] = df_repos_movs.To.apply(
                    lambda x: self.__dct_dist.get((loc, x), inf))

                df_repos_movs = df_repos_movs[
                    df_repos_movs.Dist < inf].copy()

                df_repos_movs['MovementID'] = [self.update_repos_movement_id()
                                               for i in range(df_repos_movs.shape[0])]

                df_repos_movs['DrivingTime'] = df_repos_movs.apply(lambda x: self.__get_movement_driving_time(
                    x['From'], x['To'], x['VehicleType']), axis=1)

                df_repos_movs = df_repos_movs[
                    df_repos_movs.DrivingTime < inf].copy()

                df_repos_movs = df_repos_movs[df_repos_movs.DrivingTime <=
                                              self.__max_repos_driving_time].copy()

                if df_repos_movs.empty:
                    return

                # df_repos_movs['ArrDateTime'] = df_repos_movs.apply(
                #     lambda x: x['DepDateTime'] + timedelta(minutes=x['DrivingTime']), axis=1)

                df_repos_movs['ArrDateTime'] = df_repos_movs.apply(lambda x: self.__get_arr_datetime(
                    loc1=x['From'], loc2=x['To'], vehicle=x['VehicleType'],
                    depdatetime=x['DepDateTime']), axis=1)

                df_repos_movs = df_repos_movs[
                    ~df_repos_movs.ArrDateTime.isnull()].copy()

                df_repos_movs['Utilisation'] = 0
                df_repos_movs['PayWeight'] = 0
                df_repos_movs['color_category'] = 'repos'
                df_repos_movs['draggableY'] = False
                df_repos_movs['draggableX'] = False
                df_repos_movs['tu'] = ''
                df_repos_movs['Capacity'] = 0
                df_repos_movs['is_repos'] = True
                df_repos_movs['is_adhoc'] = False
                df_repos_movs['linehaul_id'] = df_repos_movs.apply(
                    lambda x: '.'.join([str(x['From']), str(x['To']), str(x['DepDateTime'].strftime("%H%M"))]), axis=1)

                df_repos_movs['loc_string'] = ''

                df_repos_movs['n_drivers'] = 1

                df_repos_movs[
                    'MovementID'] = df_repos_movs.MovementID.astype(int)

                df_repos_movs['weighted_dist'] = df_repos_movs['Dist'] * \
                    self.__weighted_dist_val

                df_repos_movs = df_repos_movs.loc[:, [
                    'MovementID',
                    'linehaul_id',
                    'From', 'To',
                    'loc_string',
                    'VehicleType',
                    'shift',
                    'shift_id',
                    'DepDateTime',
                    'ArrDateTime',
                    'DrivingTime',
                    'tu',
                    'Dist',
                    'Capacity', 'PayWeight', 'Utilisation',
                    'is_repos', 'is_adhoc', 'weighted_dist', 'n_drivers', 'category',
                    'color_category', 'draggableY', 'draggableX']].copy()

                if df_repos_movs.empty:
                    return

                df_repos_movs['is_repos'] = df_repos_movs.is_repos.astype(bool)
                df_repos_movs['is_adhoc'] = df_repos_movs.is_adhoc.astype(bool)
                df_repos_movs['draggableY'] = df_repos_movs.draggableY.astype(
                    bool)
                df_repos_movs['draggableX'] = df_repos_movs.draggableX.astype(
                    bool)

                self.__df_repos_movements = concat(
                    [self.__df_repos_movements, df_repos_movs])

        except Exception:
            log_exception(
                popup=True, remarks=f'Building repositioning movements failed for {loc}.')

            return

    def _get_runtimes_info(self, orig, dest, vehicle, if_none={}):

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
            
        return if_none

    def __get_movement_dist(self, orig, dest, vehicle=1, warnings=True, if_none=None):

        try:
            dct_data = self.__dct_lane_info.get('|'.join([orig, dest, str(vehicle)]),
                                                self._get_runtimes_info(orig=orig, dest=dest, vehicle=vehicle, if_none={}))

            return dct_data['dist'] if dct_data else if_none
        
        except Exception:
            log_exception(popup=False, 
                          remarks=f'Getting movement distance failed for {orig}->{dest} by vehicle {vehicle}.')
        
        return if_none
        
    def __get_movement_driving_time(self, orig, dest, vehicle=1, apply_utc=0):

        dct_data = self.__dct_lane_info.get('|'.join([orig, dest, str(vehicle)]),
                                            self._get_runtimes_info(orig=orig, dest=dest, vehicle=vehicle))

        return dct_data['runtime']


    def __get_arr_datetime(self, loc1, loc2, vehicle, depdatetime):

        __dt = self.__get_movement_driving_time(
            orig=loc1, dest=loc2, vehicle=vehicle, apply_utc=1)

        if 0 < __dt < inf:
            return depdatetime + timedelta(minutes=__dt)
        else:
            return None

    def update_repos_movement_id(self):
        self.__max_repos_movement_id += 1
        return self.__max_repos_movement_id
