from os import getenv
from lion.movement.movements_manager import UI_MOVEMENTS
import lion.logger.exception_logger as xcption_logger
from pandas import to_datetime, to_timedelta, Series, DataFrame
from lion.orm.location import Location
from lion.orm.user_params import UserParams
from datetime import timedelta
from lion.utils.concat import concat
from lion.ui.ui_params import UI_PARAMS


# The purpose of this module is to identify mutual movements which can be connected
# based on a certain rule, e.g., user-set max waiting time, etc.
# Each movement has,
#     unplanned_break_time: a break time considered in the travel time of the movement,
# e.g, G410_DistanceTime table of DELTA
#     Driving time
#     Rest time: Is a longer rest time e.g., sleep after a long driving time
# We include two additional times pe rmovement when building tour: preDepTime and PostArrTime. We do not Count
# these times to calculate arrival times but we consider them for departure time. Moreover, we take them into
# account when calculating tour duration.

# Some terminologiese:
# "Planned break" is actually the waiting time between two movements while 'UnplannedBreakTime'
# is the break time which is included in the driving time such as the figures of G410_DistaneTime
# table in  DELTA database


class ConnectionTree():

    _instance = None
    _initialized = False

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance
    
    def __init__(self):
        pass

    def _initialize(self):

        self.__dct_footprint = Location.to_dict()
        self.__set_network_settings()
        self.__df_movements = DataFrame()
        self.__set_input_movements = set()
        self.__dict_all_movements = UI_MOVEMENTS.dict_all_movements
        self.__clean_up_mov_data()
        self._initialized = True
        self.__xcption_logger = xcption_logger

    def reset(self):
        self._initialized = False
        self._initialize()

    def __clean_up_mov_data(self):

        self.Object_status_OK = True
        self.__dct_loc_outbound_movs = {}
        self.__dict_con_time_extended = {}
        self.__dict_connection_time = {}
    
    @classmethod
    def get_instance(cls):
        return cls()

    @property
    def xcption_logger(self):
        return self.__xcption_logger
    
    @xcption_logger.setter
    def xcption_logger(self, x):
        self.__xcption_logger = x

    @property
    def df_movements(self):
        return self.__df_movements

    @property
    def set_input_movements(self):
        return self.__set_input_movements

    @set_input_movements.setter
    def set_input_movements(self, x):

        # Here is the main entry of the module
        self.__clean_up_mov_data()
        self.__set_input_movements = x

    @property
    def dict_con_time_string(self):
        return {'->'.join([str(int(i)) for i in k]): v
                for k, v in self.__dict_con_time_extended.items()}

    @property
    def dict_con_time_extended(self):
        return self.__dict_con_time_extended

    @property
    def dict_connection_time(self):
        return self.__dict_connection_time

    @property
    def dict_con_time_loc(self):
        return {'->'.join([
            self.__dict_all_movements[int(i)]['From'] for i in k]): v
            for k, v in self.__dict_con_time_extended.items()}

    def __set_network_settings(self):

        self.__maximum_waiting_minutes = UI_PARAMS.MAXIMUM_DOWNTIME
        self.__maxreposmin = UI_PARAMS.MAX_REPOS_DRIV_MIN

        self.Object_status_OK = True
        self.__clean_up_mov_data()

    def reset_default_network_params(self):

        try:

            self.__maxreposmin = 360
            self.__maximum_waiting_minutes = 360

            UserParams.update(maxreposdrivmin=self.__maxreposmin, maxcontime=self.__maximum_waiting_minutes)

        except Exception:
            self.__xcption_logger.log_exception(popup=False)

    def build_connection_tree(self):

        self.__set_network_settings()

        try:
            if not self.__set_input_movements:

                self.__set_input_movements = set(
                    [m for m, v in self.__dict_all_movements.items() if v.is_loaded()])

            self.__df_movements = UI_MOVEMENTS.get_all_df_movements(
                set_input_movements=self.__set_input_movements,
                maxreposmin=self.__maxreposmin)

            self.__loaded_movements = set(
                self.__df_movements[
                    self.__df_movements.is_repos.astype(int) == 0].copy().MovementID.tolist())

            [self.__build_connection_tree_per_movement(
                m) for m in self.__loaded_movements]

        except Exception:
            self.__xcption_logger.log_exception(popup=False)

    def __build_connection_tree_per_movement(self, movement_id):

        try:

            mov_loc_to = self.__dict_all_movements.get(
                movement_id, {}).get('To', '')

            mov_loc_from = self.__dict_all_movements.get(
                movement_id, {}).get('From', '')

            __movement_id_driving_time = self.__dict_all_movements[
                movement_id]['DrivingTime']

            __movement_id_depdatetime = self.__dict_all_movements[
                movement_id]['DepDateTime']

            __movement_id_arrdatetime = self.__dict_all_movements[
                movement_id]['ArrDateTime']

            # Trying to find movements which can be connected to movement_id
            df_arrivals = self.__get_inbound_movs(mov_loc_from)

            df_arrivals['Dp_MoveID'] = movement_id
            df_arrivals['Dp_MoveID_Dep_DateTime'] = __movement_id_depdatetime

            __latest_feas_arrival = __movement_id_depdatetime - \
                timedelta(minutes=int(
                    self.__dct_footprint[mov_loc_from]['turnaround_min']))

            df_arrivals = df_arrivals[
                df_arrivals.Ar_MoveID_Arr_DateTime <= __latest_feas_arrival].copy()

            df_arrivals['Dep_mov_dur'] = __movement_id_driving_time

            # Trying to find movements to which movement_id can be connected to
            df_departures = self.__get_outbound_movs(mov_loc_to)

            df_departures['Ar_MoveID'] = movement_id
            df_departures['Ar_MoveID_Arr_DateTime'] = __movement_id_arrdatetime

            __earliest_feas_departure = __movement_id_arrdatetime + timedelta(
                minutes=int(self.__dct_footprint[mov_loc_to]['turnaround_min']))

            df_departures = df_departures[
                df_departures.Dp_MoveID_Dep_DateTime >= __earliest_feas_departure].copy()

            df_departures[
                'Arr_mov_dur'] = __movement_id_driving_time

            df_arrivals = df_arrivals.loc[:,
                                          df_departures.columns.tolist()].copy()

            df_merged_dep_arr = concat(
                df_list=[df_departures, df_arrivals], ignore_index=True)

            _is_not_isolated_movement = not (
                df_departures.empty and df_arrivals.empty)

            if df_merged_dep_arr.empty and _is_not_isolated_movement:

                df_departures.reset_index(inplace=True)
                df_departures.drop(['index'], inplace=True, axis=1)

                df_arrivals.reset_index(inplace=True)
                df_arrivals.drop(['index'], inplace=True, axis=1)

                df_departures['Dp_MoveID'] = df_departures['Dp_MoveID'].astype(
                    int)
                df_departures['Ar_MoveID'] = df_departures['Ar_MoveID'].astype(
                    int)
                df_departures['Dep_mov_dur'] = df_departures['Dep_mov_dur'].astype(
                    int)
                df_departures['Arr_mov_dur'] = df_departures['Arr_mov_dur'].astype(
                    int)

                df_departures['Dp_MoveID_Dep_DateTime'] = df_departures.Dp_MoveID_Dep_DateTime.apply(
                    lambda x: to_datetime(x))

                df_departures['Ar_MoveID_Arr_DateTime'] = df_departures.Ar_MoveID_Arr_DateTime.apply(
                    lambda x: to_datetime(x))

                df_arrivals['Dp_MoveID'] = df_arrivals['Dp_MoveID'].astype(
                    int)
                df_arrivals['Ar_MoveID'] = df_arrivals['Ar_MoveID'].astype(
                    int)
                df_arrivals['Dep_mov_dur'] = df_arrivals['Dep_mov_dur'].astype(
                    int)
                df_arrivals['Arr_mov_dur'] = df_arrivals['Arr_mov_dur'].astype(
                    int)

                df_arrivals['Dp_MoveID_Dep_DateTime'] = df_arrivals.Dp_MoveID_Dep_DateTime.apply(
                    lambda x: to_datetime(x))

                df_arrivals['Ar_MoveID_Arr_DateTime'] = df_arrivals.Ar_MoveID_Arr_DateTime.apply(
                    lambda x: to_datetime(x))

                df_merged_dep_arr = concat(
                    df_list=[df_departures, df_arrivals], ignore_index=True)

            if df_merged_dep_arr.empty and _is_not_isolated_movement:

                _err = f'No connection was found for {movement_id}!'
                _err = f'{
                    _err}This error might be caused by miss-alignment in datatypes or columns of '
                _err = f'{
                    _err}dataframe to be concatenicated. Make sure columns are identical and have identical '
                _err = f'{
                    _err}data types. It could also be due to parameters such as maximum empty movement duration or downtime'

                from pandas import concat as pd_concat

                try:
                    df_merged_dep_arr = pd_concat(
                        [df_departures, df_arrivals], ignore_index=True)
                except Exception as err:
                    df_merged_dep_arr = DataFrame()
                    _err = f'{_err}. \n{str(err)}'

                if df_merged_dep_arr.empty:
                    raise Exception(_err)

            if not df_merged_dep_arr.empty:

                w_series = df_merged_dep_arr['Dp_MoveID_Dep_DateTime'] - \
                    df_merged_dep_arr['Ar_MoveID_Arr_DateTime']

                df_merged_dep_arr['connection_time'] = Series(
                    to_timedelta(w_series, unit='d')).dt.total_seconds().divmod(60)[0]

                df_merged_dep_arr = df_merged_dep_arr[
                    df_merged_dep_arr.connection_time <= self.__maximum_waiting_minutes].copy()

            if not df_merged_dep_arr.empty:

                df_merged_dep_arr['Time'] = df_merged_dep_arr[
                    'connection_time'] + df_merged_dep_arr['Dep_mov_dur']

                df_merged_dep_arr = df_merged_dep_arr[
                    ~df_merged_dep_arr.Time.isna()].copy()

                df_merged_dep_arr['Time'] = df_merged_dep_arr.Time.astype(
                    int)

                df_merged_dep_arr.set_index(
                    ['Ar_MoveID', 'Dp_MoveID'], inplace=True)

                self.__dict_con_time_extended.update(
                    df_merged_dep_arr.Time.to_dict())

                self.__dict_connection_time.update(
                    df_merged_dep_arr.connection_time.to_dict())

            del df_merged_dep_arr

        except Exception:
            self.__xcption_logger.log_exception(popup=False,
                           remarks=f'Building connection tree for {movement_id} failed!')

    def __get_outbound_movs(self, loc):

        try:
            df_movs = self.__df_movements.loc[self.__df_movements.From == loc, [
                'MovementID', 'DepDateTime', 'DrivingTime']].copy()

            df_movs.rename(columns=(
                {'MovementID': 'Dp_MoveID',
                    'DepDateTime': 'Dp_MoveID_Dep_DateTime',
                    'DrivingTime': 'Dep_mov_dur'}), inplace=True)

        except Exception:
            df_movs = DataFrame()

        self.__dct_loc_outbound_movs.update({loc: df_movs})

        return df_movs

    def __get_inbound_movs(self, loc):

        try:
            df_movs = self.__df_movements.loc[
                self.__df_movements.To == loc, ['MovementID', 'ArrDateTime', 'DrivingTime']].copy()

            df_movs.rename(columns=(
                {'MovementID': 'Ar_MoveID',
                    'ArrDateTime': 'Ar_MoveID_Arr_DateTime',
                    'DrivingTime': 'Arr_mov_dur'}), inplace=True)

        except Exception:
            df_movs = DataFrame()

        return df_movs

CONNECTION_TREE = ConnectionTree.get_instance()