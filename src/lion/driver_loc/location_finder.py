from collections import defaultdict
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.orm.drivers_info import DriversInfo
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.utils.if_none import if_none
from lion.logger.exception_logger import log_exception
from lion.utils.order_dict_by_value import order_dict_by_value
from lion.orm.user_params import UserParams
from lion.orm.location import Location
from numpy import inf
from lion.utils.dfgroupby import groupby as df_groupby
from lion.utils.sqldb import SqlDb

class LocationFinder():

    def __init__(self, dct_drivers={}):

        try:

            dct_footprint = Location.to_dict()

            self.__driver_dt_threshold = 270

            self.__excluded_locs = UserParams.get_param(
                param='excluded_locs', if_null='').split(';')
            
            self.__excluded_locs.extend(
                ['QQM','SCS','EDI','EMA','INV','QQN','XNE', 'HRT','UHF', 'BFS','BF4', 'CVT'])

            self.__list_non_customer_locs = [
                x for x in dct_footprint.keys() if dct_footprint[x][
                    'loc_type'].lower() in ['hub', 'station', 'gateway']]

            self.__list_all_locs = list(dct_footprint)

            del dct_footprint

            if not dct_drivers:
                dct_drivers = DriversInfo.to_dict()

            self.__dct_drivers = dct_drivers
            self.__dct_loc_drivers = {}
            self.__set_driver_locs = set()
            self.__dct_close_by_driver_locs = {}

            if self.__dct_drivers:
                self.__set_dct_driver()

        except:
            log_exception(
                popup=True, remarks='CloseByLocs could not be initialised!')

    @property
    def dct_loc_drivers(self):
        return {lc: len(
            self.__dct_loc_drivers[lc]) for lc in self.__dct_loc_drivers}

    @property
    def dct_drivers(self):
        return self.__dct_drivers

    @dct_drivers.setter
    def dct_drivers(self, x):
        self.__dct_drivers = x
        self.__set_dct_driver()

    @property
    def dct_driver_count_per_cluster(self):
        return self.__dct_driver_count_per_cluster

    @property
    def dct_close_by_driver_locs(self):
        if not self.__dct_close_by_driver_locs:
            self.__calc_dct_closeby_drivers()

        return dict(self.__dct_close_by_driver_locs)

    @property
    def dct_drivers_within_maxreposdir(self):
        return dict(self.__dct_drivers_within_maxreposdir)

    def clear_dct_close_by_driver_locs(self):
        self.__dct_close_by_driver_locs = {}

    def __set_dct_driver(self):

        try:

            if not self.__dct_drivers:
                raise Exception('dct_drivers is Empty!')

            self.__set_driver_locs = set([self.__dct_drivers[d]['loc']
                                          for d in set(self.__dct_drivers)])

            __dct_loc_drivers = defaultdict(list)
            for lc in self.__set_driver_locs:
                __dct_loc_drivers[lc] = [
                    d for d, v in self.__dct_drivers.items() if v['loc'] == lc]

            self.__dct_loc_drivers = dict(__dct_loc_drivers)

            self.__set_eligable_driver_locs = self.__set_driver_locs.copy()
            # self.__set_eligable_driver_locs = set([x for x in self.__set_driver_locs if x in self.__list_non_customer_locs])

            self.__calc_dct_closeby_drivers()

        except:
            log_exception(popup=True, remarks='Setting dct_drivers failed!')

    def read_location_params(self):

        try:

            df_loc_params = SqlDb().sqlalchemy_select(
                tablename='loc_params', bind='lion_db')

            df_loc_params = df_loc_params[df_loc_params.active == 1].copy()

            self.__list_all_locs = list(set(df_loc_params.loc_code.tolist()))

            df_loc_params['max_allowed_resources'] = df_loc_params.apply(
                lambda x: max(0, int(x['un_fixed_employed'] + x['un_fixed_subco'] +
                                     x['extra_employed'] + x['extra_subco'])), axis=1)

            df_driver_loc_param = df_loc_params[
                df_loc_params.max_allowed_resources > 0].copy()

            if df_driver_loc_param.empty:

                df_driver_loc_param = df_loc_params[
                    df_loc_params.loc_code.isin(self.__list_non_customer_locs)].copy()

                OPT_LOGGER.log_statusbar(
                    "Default driver locations will be used, i.e, hub, station and gateway.")

            __Cols_value = ['un_fixed_employed', 'un_fixed_subco',
                            'extra_employed', 'extra_subco', 'max_allowed_resources']

            df_driver_loc_param = df_groupby(df_driver_loc_param, groupby_cols=['loc_code'],
                                       agg_cols_dict={c: 'max' for c in __Cols_value}).copy()

            self.__set_driver_locs = set(df_driver_loc_param.loc_code.tolist())
            self.__set_eligable_driver_locs = set(
                [x for x in self.__set_driver_locs if x in self.__list_non_customer_locs])

            del df_driver_loc_param, df_loc_params

        except Exception:
            self.__set_driver_locs = set()
            self.__set_eligable_driver_locs = set()
            log_exception(popup=False)

    def __calc_dct_closeby_drivers(self):
        """
        In this model, we build a lookup dict for drivers
        within driving_time_threshold driving time from a location.
        This can be useful when trying to evaluate drivers within certain
        driving time
        """

        
        try:

            self.__dct_close_by_driver_locs = defaultdict(list)
            if not self.__set_driver_locs:
                raise Exception('The set of driver locations was empty!')

            if self.__excluded_locs:

                for loc in self.__excluded_locs:
                    if loc in self.__set_driver_locs:
                        self.__set_driver_locs.remove(loc)

                for loc in self.__excluded_locs:
                    if loc in self.__set_eligable_driver_locs:
                        self.__set_eligable_driver_locs.remove(loc)

            while self.__list_all_locs:

                __loc = self.__list_all_locs.pop()
                __dct_driving_time = defaultdict()

                for x in self.__set_eligable_driver_locs:

                    __driving_time = if_none(UI_RUNTIMES_MILEAGES.get_movement_driving_time(
                        orig=__loc, dest=x), inf)

                    if __driving_time <= self.__driver_dt_threshold:
                        __dct_driving_time[x] = __driving_time

                if __loc in self.__set_driver_locs:
                    __dct_driving_time[__loc] = 0

                if __dct_driving_time:

                    __dct_driving_time = order_dict_by_value(
                        dct=__dct_driving_time, asc=True)

                    self.__dct_close_by_driver_locs[__loc].extend(
                        list(__dct_driving_time))

        except Exception:
            log_exception(popup=False,
                           remarks='Warnning! __dct_close_by_driver_locs might be empty!')
