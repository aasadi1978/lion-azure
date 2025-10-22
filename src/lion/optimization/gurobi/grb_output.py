from collections import defaultdict


class GrbOutput():

    def __init__(self):
        self.__optimal_tours = {}
        self.__set_optimized_input_movements = set()
        self.__dct_loc_driver_count = defaultdict()

    @property
    def optimal_tours(self):
        return self.__optimal_tours

    @optimal_tours.setter
    def optimal_tours(self, x):
        self.__optimal_tours = x

    @property
    def optimal_drivers(self):
        return self.__optimal_drivers

    @optimal_drivers.setter
    def optimal_drivers(self, x):
        self.__optimal_drivers = x

    @property
    def set_optimized_input_movements(self):
        return self.__set_optimized_input_movements

    @set_optimized_input_movements.setter
    def set_optimized_input_movements(self, x):
        self.__set_optimized_input_movements = x

    @property
    def dct_loc_driver_count(self):
        return self.__dct_loc_driver_count

    @dct_loc_driver_count.setter
    def dct_loc_driver_count(self, x):
        self.__dct_loc_driver_count = x

    @property
    def selected_drivers_tour_pairs(self):
        return self.__selected_drivers_tour_pairs

    @selected_drivers_tour_pairs.setter
    def selected_drivers_tour_pairs(self, x):

        self.__optimal_tours = {}
        self.__selected_drivers_tour_pairs = x
        for P in self.__selected_drivers_tour_pairs:

            __t = P[1]
            __d = P[0]

            self.__dct_loc_driver_count[
                __d] = self.__dct_loc_driver_count.get(__d, 0) + 1

            self.__optimal_tours.update(
                {__t: self.__dict_tours[__t][__d]})

        self.__dct_loc_driver_count = dict(self.__dct_loc_driver_count)
        self.__dct_loc_driver_count = {
            k: v for k, v in self.__dct_loc_driver_count.items() if v > 0}
