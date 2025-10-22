from collections import defaultdict
from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.orm.drivers_info import DriversInfo
from lion.logger.exception_logger import log_exception
from lion.utils.order_dict_by_value import order_dict_by_value
from lion.utils.safe_copy import secure_copy

class ProposedLocationsOptimizer:

    def __init__(self):

        self._dct_recommended_movements_per_driver_loc = defaultdict(set)
        self._dct_drivers_count_per_loc = DriversInfo.get_drivers_count_per_loc()

        self._dict_movements_to_optimize = OPT_PARAMS.DCT_MOVEMENTS_TO_OPTIMIZE
        self._dct_close_by_driver_locs = OPT_PARAMS.DCT_CLOSE_BY_DRIVER_LOCS
        self.__status = ''

        if not self._dct_drivers_count_per_loc:
            self._dct_drivers_count_per_loc = {loc: OPT_PARAMS.LOC_CAPACITY_LIMIT 
                                               for loc in self._dct_close_by_driver_locs.keys()}

    def get_proposed_locs_for_movement(self):

        if not self._dict_movements_to_optimize:
            OPT_PARAMS.DCT_RECOMMENDED_MOVEMENTS_PER_DRIVER_LOC = defaultdict(set)
            return

        for movement_id in set(self._dict_movements_to_optimize):

            try:

                list_close_by_locs = self._dct_close_by_driver_locs.get(
                    self._dict_movements_to_optimize[movement_id]['From'], [])

                list_close_by_locs = list_close_by_locs[: min(len(list_close_by_locs), OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC)]

                if list_close_by_locs:
                    while list_close_by_locs:
                        self._dct_recommended_movements_per_driver_loc[
                            list_close_by_locs.pop()].update([movement_id])

                list_close_by_locs = self._dct_close_by_driver_locs.get(
                    self._dict_movements_to_optimize[movement_id]['To'], [])

                list_close_by_locs = list_close_by_locs[: min(len(list_close_by_locs), OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC)]

                if list_close_by_locs:
                    while list_close_by_locs:
                        self._dct_recommended_movements_per_driver_loc[
                            list_close_by_locs.pop()].update([movement_id])

            except Exception:

                if self.__status:
                    self.__status=f"{self.__status}. {log_exception(popup=False, 
                                remarks=f'Getting propsoed locs failed for {movement_id}.')}"
                else:
                    self.__status = log_exception(popup=False, 
                                remarks=f'Getting propsoed locs failed for {movement_id}.')
        

        if self.__status:
            OPT_LOGGER.log_info(
                message=f'Movements with no recommendations have been processed! {self.__status}')

        dct_recommended_movements_per_driver_loc = secure_copy(OPT_PARAMS.DCT_RECOMMENDED_MOVEMENTS_PER_DRIVER_LOC)
        dct_recommended_movements_per_driver_loc.update(self._dct_recommended_movements_per_driver_loc)
        dct_recommended_movements_per_driver_loc = secure_copy({loc: set(list(v)[:min(len(v), OPT_PARAMS.LOC_CAPACITY_LIMIT)]) 
                                                     for loc, v in dct_recommended_movements_per_driver_loc.items()})

        OPT_PARAMS.DCT_RECOMMENDED_MOVEMENTS_PER_DRIVER_LOC=secure_copy(dct_recommended_movements_per_driver_loc)

        del dct_recommended_movements_per_driver_loc
