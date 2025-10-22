from copy import deepcopy
from datetime import timedelta
from lion.orm.drivers_info import DriversInfo
from lion.logger.exception_logger import log_exception
from lion.bootstrap.constants import LOC_STRING_SEPERATOR


class DictMovement(dict):

    def __init__(self, **dct_mov):
        """
        use enhanced_dict = DictMovement(**dct_data)
        This will be passed as dict to kwargs. Use DictMovement(**dct_data, kyword1=1, kyword2=2) to add more kywords
        but make sure pop them before sending to super()
        """

        super().__init__(**dct_mov)

    def __eq__(self, dct_other_movement):

        if not isinstance(dct_other_movement, DictMovement):
            return NotImplemented

        return (
            self['str_id'] == dct_other_movement['str_id'] and
            self['MovementID'] == dct_other_movement['MovementID']
        )

    def __ne__(self, dct_other_movement):

        if not isinstance(dct_other_movement, DictMovement):
            return NotImplemented

        return (
            self['str_id'] != dct_other_movement['str_id'] or
            self['MovementID'] != dct_other_movement['MovementID']
        )

    @property
    def movement_id(self):
        return self['MovementID']

    @movement_id.setter
    def movement_id(self, x):
        self['MovementID'] = x

    @property
    def dep_date_time(self):
        return self.__dep_date_time

    @dep_date_time.setter
    def dep_date_time(self, x):
        self.__dep_date_time = x
        self.__apply_new_datetime()

    @property
    def shift(self):
        self.__shift = DriversInfo.get_shift_name(
            shift_id=self['shift_id'])
        self['shift'] = self.__shift
        return self.__shift

    @shift.setter
    def shift(self, x):
        self.__shift = x
        self['shift'] = x

    @property
    def shift_id(self):
        return self.get('shift_id', 0)

    @shift_id.setter
    def shift_id(self, x):
        self['shift_id'] = x

    @ property
    def weekday(self):
        return self.__weekday

    @ weekday.setter
    def weekday(self, x):
        self.__weekday = x
        self['weekday'] = x

    @ property
    def str_id(self):
        return self.get('str_id', self.update_str_id())

    @ property
    def linehaul_id(self):
        return self.create_linehaul_id()

    def is_loaded(self):
        return not (self['TrafficType'].lower() == 'empty')

    def is_repos(self):
        return self['TrafficType'].lower() == 'empty'

    def update_items(self, **kwargs):
        for k, v in kwargs.items():
            self.update({k: v})

    @ property
    def changeover_string(self):
        if len(self['loc_string'].split(LOC_STRING_SEPERATOR)) >= 4:
            return self['loc_string']
        else:
            return ''

    @property
    def tu(self):

        if 'tu' not in self.keys():
            self['tu'] = ''

        return self['tu']

    @property
    def loc_string(self):
        try:
            if self['loc_string']:
                return self['loc_string']

            self.create_linehaul_id()
            return self['linehaul_id']

        except Exception:
            strMsg = log_exception(popup=False)
            return f'ERROR: {strMsg}'

    @property
    def driving_time(self):
        return self['DrivingTime']

    @property
    def extended_str_id(self):
        self['extended_str_id'] = f"{self['str_id']}|{self['MovementID']}"
        return self['extended_str_id']

    def is_changeover(self):
        """
        Determines if the location string represents a changeover.

        Returns:
            bool: True if the location string has more than 3 segments separated by dots, False otherwise.
        """
        try:
            return len(self.loc_string.split('.')) > 3
        except Exception:
            return False

    def update_str_id(self):
        """
        Updates the 'str_id' attribute of the object based on certain conditions.

        Returns:
            str: The updated 'str_id' value.

        Raises:
            Exception: If 'DepDateTime' is not found in the keys.

        """
        try:
            _str_id = ''

            if 'DepDateTime' not in self:
                raise Exception("Datetime was not found in the keys!")

            depday = int(self.get('weekday', 'Mon') !=
                         self['DepDateTime'].strftime("%a"))

            _str_id = f"{_str_id}{self['From']}|{self['To']}|{depday}"

            deptime = self['DepDateTime'].strftime("%H%M")

            _str_id = f"{_str_id}|{deptime}"

            self['str_id'] = f"{_str_id}|{
                self['VehicleType']}|{self['TrafficType']}"

            self['leg'] = self['leg'] if 'leg' in self.keys() else 1
            self['legs'] = self['legs'] if 'legs' in self.keys() else 1

        except Exception:
            log_exception(popup=False, remarks="str_id could not be created!")
            return ''

        return _str_id

    def create_linehaul_id(self):

        try:
            _strid_keys = ['From', 'To', 'DepTime']

            values = []
            if 'DepDateTime' not in self:
                raise Exception(f"Datetime was not found in the keys!")

            self['DepTime'] = self['DepDateTime'].strftime("%H%M")

            for key in _strid_keys:
                values.append(str(self[key]))

            self.update({'linehaul_id': '.'.join(values)})

            return '.'.join(values)

        except Exception:
            log_exception(
                popup=False, remarks=f"__get_lhid could not be created!")

            return ''

    def modify_dep_day(self, wkday):

        try:

            wkdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ndays = wkdays.index(wkday) - \
                wkdays.index(self.get('weekday', 'Mon'))

            self['shift_id'] = self.get('shift_id', 0)

            self['DepDateTime'] = self['DepDateTime'] + timedelta(days=ndays)
            self['ArrDateTime'] = self['ArrDateTime'] + timedelta(days=ndays)

        except Exception:

            log_exception(
                popup=True, remarks=f"modify_dep_day Failed!")

    def get_modified_dep_datetimes(self, wkday):

        try:

            m_wkday = self.get('weekday', 'Mon')

            if wkday == m_wkday:
                return self['DepDateTime']

            wkdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ndays = wkdays.index(wkday) - \
                wkdays.index(self.get('weekday', m_wkday))

            return self['DepDateTime'] + timedelta(days=ndays)

        except Exception:
            log_exception(
                popup=True, remarks=f"get_modified_dep_datetimes Failed!")

        return None

    def get_modified_arr_datetimes(self, wkday):

        try:

            m_wkday = self.get('weekday', 'Mon')

            if wkday == m_wkday:
                return self['ArrDateTime']

            wkdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ndays = wkdays.index(wkday) - \
                wkdays.index(self.get('weekday', m_wkday))

            return self['ArrDateTime'] + timedelta(days=ndays)

        except Exception:
            log_exception(
                popup=True, remarks=f"get_modified_arr_datetimes Failed!")

        return None

    def __apply_new_datetime(self):

        # create a backup of self before making changes

        self_copy = deepcopy(self)
        try:

            __dt1 = self['DepDateTime']

            if self.__dep_date_time >= __dt1:
                __total_minutes = int(
                    (self.__dep_date_time - __dt1).total_seconds()/60 + 0.5)
            else:
                __total_minutes = -1 * int(
                    (__dt1 - self.__dep_date_time).total_seconds()/60 + 0.5)

            self['DepDateTime'] = self.__dep_date_time

            self['ArrDateTime'] = self['ArrDateTime'] + \
                timedelta(minutes=__total_minutes)

            # __locstr = self['loc_string']
            # lst_strng = __locstr.split(loc_string_seperator)
            # lst_strng.pop()
            # lst_strng.append(self.__dep_date_time.strftime("%H%M"))

            # self['loc_string'] = loc_string_seperator.join(lst_strng)

            # self['linehaul_id'] = '.'.join(
            #     [self['From'], self['To'], self.__dep_date_time.strftime("%H%M")])

        except Exception:
            self = self_copy
            log_exception(popup=False)

        del self_copy
        self.update_str_id()
