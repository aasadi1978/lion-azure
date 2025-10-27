from collections import defaultdict
import logging

from lion.orm.location import Location
from lion.orm.location_mapping import LocationMapper
from lion.orm.orm_runtimes_mileages import RuntimesMileages
from lion.logger.exception_logger import log_exception
from lion.utils.roundup_to_nearest_5 import roundup_to_nearest_5


class RuntimeMileageFetcher():

    _instance = None

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self):
        pass

    def __initialize(self):
        try:
            self.__dict_dist_time = defaultdict(lambda: defaultdict(dict))
            self.__dict_dist_time.update(RuntimesMileages.to_dict())
            self.__user_dt_scenario = 'Default'
            self._initialized = True
        except Exception:
            self._initialized = False
            log_exception()

    def initialize(self):
        if not self._initialized:
            self.__initialize()

    def reset(self):
        RuntimesMileages.clear_cache()
        self._initialized = False
        self.__initialize()
    
    @classmethod
    def get_instance(cls):
        return cls()

    def retrieve_travel_time_and_distance(self, orig, dest, vehicle=1):

        try:
            dct = self.__dict_dist_time[orig][dest][vehicle]
            runtime = dct.get('runtime', None)
            dist = dct.get('dist', None)

            if runtime is not None and dist is not None:
                return runtime, dist
            
        except Exception as e:

            runtime = None
            dist = None

        try:

            if runtime is None:
                runtime = self.get_movement_driving_time(orig, dest, vehicle=vehicle)
            
            if dist is None:
                dist = self.get_movement_dist(orig, dest, vehicle=vehicle)

            if Location.is_colocated(orig, dest):
                
                self.__dict_dist_time[orig][dest][vehicle] = {'runtime': 5, 'dist': 1}
                runtime = 5
                dist = 1

                return runtime, dist

            if LocationMapper.is_mapped(loc_code1=orig, loc_code2=dest):
                return None, None

            if runtime is not None and dist is not None:
                self.__dict_dist_time[orig][dest][vehicle] = {'runtime': runtime, 'dist': dist}
                return runtime, dist

            runtime, dist = RuntimesMileages.query_runtime_mileage(orig=orig, dest=dest, vehicle=vehicle)

            if runtime and dist:
                runtime = roundup_to_nearest_5(runtime)
                self.__dict_dist_time[orig][dest][vehicle] = {'runtime': runtime, 'dist': dist}
            
            return runtime, dist

        except Exception as e:
            log_exception(popup=True, 
                          remarks=f"Error occured when pulling dist and runtime for {orig}->{dest} using vehicle {vehicle}: {e}")

        return None, None

    def get_movement_driving_time(self, orig, dest, vehicle=1, apply_utc=0):

        vehicle = 4 if vehicle == 4 else 1
        try:

            runtime, _ = RuntimesMileages.get_dist_runtime(orig=orig, dest=dest, vehicle=vehicle)
            if runtime is not None:
                return roundup_to_nearest_5(runtime)

            val = RuntimesMileages.get_runtime(
                orig=orig, dest=dest, vehicle=vehicle, scenario=self.__user_dt_scenario)

            val = roundup_to_nearest_5(val)

            if val is not None:
                return val

            val = RuntimesMileages.get_runtime(
                orig=dest, dest=orig, vehicle=vehicle, scenario=self.__user_dt_scenario)

            if val is not None:
                val = roundup_to_nearest_5(val)
                return val

            if vehicle == 4:

                val = RuntimesMileages.get_runtime(
                    orig=orig, dest=dest, vehicle=1, scenario=self.__user_dt_scenario)

                if val:
                    val = roundup_to_nearest_5(val * 0.8)
                    return val

                val = RuntimesMileages.get_runtime(
                    orig=dest, dest=orig, vehicle=1, scenario=self.__user_dt_scenario)

                if val:
                    val = roundup_to_nearest_5(val * 0.8)
                    return val

            if vehicle == 1:

                val = RuntimesMileages.get_runtime(
                    orig=orig, dest=dest, vehicle=4, scenario=self.__user_dt_scenario)

                if val:
                    val = roundup_to_nearest_5(val * 1.2)
                    return val

                val = RuntimesMileages.get_runtime(
                    orig=dest, dest=orig, vehicle=4, scenario=self.__user_dt_scenario)

                if val:
                    val = roundup_to_nearest_5(val * 1.2)
                    return val

        except Exception:
            log_exception(
                popup=True, remarks=f"Error occured when pulling runtimes for {orig}->{dest}")

            if str(orig) == str(dest):
                return 0

        if str(orig) == str(dest):
            return 0

        return None

    def get_movement_dist(self, orig, dest, vehicle=1, warnings=True):

        vehicle = 4 if vehicle == 4 else 1
        try:

            _, dist = RuntimesMileages.get_dist_runtime(orig=orig, dest=dest, vehicle=vehicle)
            if dist is not None:
                return max(dist, 1)

            val = RuntimesMileages.get_mileage(
                orig=orig, dest=dest, vehicle=vehicle, scenario=self.__user_dt_scenario)

            if val is not None:
                return max(val, 1)

            val = RuntimesMileages.get_mileage(
                orig=dest, dest=orig, vehicle=vehicle, scenario=self.__user_dt_scenario)
            if val is not None:
                return max(val, 1)

            if vehicle == 4:

                val = RuntimesMileages.get_mileage(
                    orig=orig, dest=dest, vehicle=1, scenario=self.__user_dt_scenario)

                if val is not None:
                    return max(val, 1)

                val = RuntimesMileages.get_mileage(
                    orig=dest, dest=orig, vehicle=1, scenario=self.__user_dt_scenario)

                if val is not None:
                    return max(val, 1)

            if vehicle == 1:

                val = RuntimesMileages.get_mileage(
                    orig=orig, dest=dest, vehicle=4, scenario=self.__user_dt_scenario)

                if val is not None:
                    return max(val, 1)

                val = RuntimesMileages.get_mileage(
                    orig=dest, dest=orig, vehicle=4, scenario=self.__user_dt_scenario)

                if val is not None:
                    return max(val, 1)

        except Exception:
            log_exception(
                popup=False, remarks=f"No mileages was found from {orig} to {dest} using {vehicle}")

        return None

UI_RUNTIMES_MILEAGES = RuntimeMileageFetcher.get_instance()