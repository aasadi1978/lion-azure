class GrbInputData():

    def __init__(self):
        self.__dict_tours = {}
        self.__dct_max_n_drivers_per_loc_in_sample = {}

    @classmethod
    def get_instance(cls):
        return cls()
    
    def reset(self):
        self.__dict_tours = {}
        self.__dct_max_n_drivers_per_loc_in_sample = {}

    @property
    def dict_tours(self):
        return self.__dict_tours

    @dict_tours.setter
    def dict_tours(self, x):
        self.__dict_tours = x

    @property
    def dct_max_n_drivers_per_loc_in_sample(self):
        """
        This data covers the total number of drivers per subset of tours to be optimized, whilst, dct_n_drivers_per_driver_location
        the total number of drivers per location in the whole network based on the latest schedule
        """
        return self.__dct_max_n_drivers_per_loc_in_sample

    @dct_max_n_drivers_per_loc_in_sample.setter
    def dct_max_n_drivers_per_loc_in_sample(self, x):
        self.__dct_max_n_drivers_per_loc_in_sample = x

GUROBI_INPUT_DATA = GrbInputData.get_instance()