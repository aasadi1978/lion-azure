from datetime import datetime, timedelta


class ElapsedTime():

    _instance=None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        pass

    def reset(self):

        self.__time_stamp = datetime.now()
        self.__dct_duration = {}

    @classmethod
    def get_instance(cls):
        return cls()
    
    @property
    def time_stamp(self):
        return self.__time_stamp

    @time_stamp.setter
    def time_stamp(self, ts):
        self.__time_stamp = ts

    @property
    def dct_duration(self):
        return self.__dct_duration

    def minutes(self, datefrom, dateto):

        total_seconds = (dateto - datefrom).total_seconds()
        return int(total_seconds/60 + 0.5)

        # t = divmod(total_seconds, 31536000) # for year calculation
        # t = divmod(total_seconds, 86400) # for days calculation

    def collapsed_minutes(self, sec=None):

        if sec is None:
            sec = (datetime.now() - self.__time_stamp).total_seconds()

        return str(timedelta(seconds=sec)).split('.')[0]

    def collapsed_time(self, total_scnds=None, datefrom=None, dateto=None):

        self.__dct_duration = {}

        if total_scnds is None:

            if datefrom is None:
                datefrom = self.__time_stamp

            if dateto is None:
                dateto = datetime.now()

            total_scnds = (dateto - datefrom).total_seconds()

        output_str = ''
        total_mseconds = total_scnds * 1000

        __yr = list(divmod(total_mseconds, 31540000000))
        __y = int(__yr[0])
        if __y > 0:
            self.__dct_duration['year'] = __y
            output_str = output_str + str(__y) + ' years; '

        __dys = list(divmod(__yr[1], 86400000))
        __d = int(__dys[0])
        if __d > 0:
            self.__dct_duration['days'] = __d
            output_str = output_str + str(__d) + ' days; '

        __hrs = list(divmod(__dys[1], 3600000))
        __h = int(__hrs[0])
        if __h > 0:
            self.__dct_duration['hours'] = __h
            output_str = output_str + str(__h) + ' hours; '

        __mins = list(divmod(__hrs[1], 60000))
        __m = int(__mins[0])
        if __m > 0:
            self.__dct_duration['minutes'] = __m
            output_str = output_str + str(__m) + ' minutes; '

        __scnds = list(divmod(__mins[1], 1000))
        __s = int(__scnds[0])
        if __s > 0:
            self.__dct_duration['seconds'] = __s
            output_str = output_str + str(__s) + ' seconds; '

        __ms = int(__scnds[1])
        if __ms > 0:
            self.__dct_duration['miliseconds'] = __ms
            output_str = output_str + str(__ms) + ' miliseconds; '

        return output_str

ELAPSED_TIME = ElapsedTime.get_instance()