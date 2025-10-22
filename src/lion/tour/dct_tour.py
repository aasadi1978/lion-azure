from pandas import Timestamp
from datetime import timedelta
from lion.orm.user_params import UserParams
from lion.utils.is_loaded import IsLoaded
from lion.logger.exception_logger import log_exception
from lion.bootstrap.constants import MOVEMENT_DUMP_AREA_NAME, RECYCLE_BIN_NAME


class DctTour(dict):

    def __init__(self, **dct_tour_data):

        if dct_tour_data:

            if 'driver_loc_mov_type_key' not in dct_tour_data.keys():

                dct_tour_data['driver_loc_mov_type_key'] = dct_tour_data[
                    'dep_date_time'].strftime('%H%M') + '->' + \
                    dct_tour_data['tour_loc_string'] + '->' + \
                    dct_tour_data['arr_date_time'].strftime('%H%M')

            if 'list_tour_movements' in dct_tour_data.keys():
                dct_tour_data['list_movements'] = dct_tour_data.pop(
                    'list_tour_movements', [0])[1:]

            if '(m, t)' in dct_tour_data.keys():
                dct_tour_data['movement_shift_pair'] = dct_tour_data.pop(
                    '(m, t)', [])

            if 'driver' in dct_tour_data.keys():
                dct_tour_data['shiftname'] = dct_tour_data['driver']

            dct_tour_data['total_dist'] = dct_tour_data.get('tour_repos_dist', 0) + \
                dct_tour_data.get('tour_input_dist', 0)

            super().__init__(**dct_tour_data)

            for ky, val in dct_tour_data.items():
                setattr(self, ky, val)

    @property
    def shiftname(self):
        self.__shiftname = self.get('shiftname', self['driver'])
        self['shiftname'] = self.__shiftname
        return self.__shiftname
    
    @property
    def tourLocString(self):

        try:
            _driver_loc_mov_type_key = self.get('driver_loc_mov_type_key', '')
            lcs = _driver_loc_mov_type_key.split('->')

            if lcs:

                lcs.pop(0)
                lcs.pop()

                return '->'.join(lcs)
            
            raise ValueError('No _driver_loc_mov_type_key found!')

        except Exception:
            log_exception(popup=False, remarks='tourLocString failed!')
            
        return ''
    
    @property
    def list_loaded_movements(self):

        _list_movements = self.get('list_loaded_movements', [])
        if not _list_movements:
            _list_movements = self.get(
                'list_movements', self.get('list_tour_movements', []))

        self['list_loaded_movements'] = [
            m for m in _list_movements if IsLoaded(m).loaded]

        return self['list_loaded_movements']

    @list_loaded_movements.setter
    def list_loaded_movements(self, lstm):
        self['list_loaded_movements'] = lstm

    @property
    def is_blank(self):
        return len(self['list_loaded_movements']) == 0

    @shiftname.setter
    def shiftname(self, shname):

        self.__shiftname = shname
        self['shiftname'] = self.__shiftname
        self['driver'] = self.__shiftname

    @property
    def weekday(self):
        return self.get('weekday', '')

    @weekday.setter
    def weekday(self, wkday):
        self['weekday'] = wkday

    @property
    def time_utilisation(self):
        maxtourdur = UserParams.get_param('maxtourdur', if_null=720)
        self['time_utilisation'] = self.get(
            'input_driving_time', 0) * 100/maxtourdur

        return self['time_utilisation']

    @time_utilisation.setter
    def time_utilisation(self, val):
        self['time_utilisation'] = val

    @property
    def shift_id(self):

        self.__shift_id = self.get('shift_id', 0)
        if self['driver'] == MOVEMENT_DUMP_AREA_NAME:
            return 1
        elif self['driver'] == RECYCLE_BIN_NAME:
            return 2

        return self.__shift_id

    @shift_id.setter
    def shift_id(self, value):

        self.__shift_id = value

        if self['driver'] not in [MOVEMENT_DUMP_AREA_NAME, RECYCLE_BIN_NAME]:
            self['shift_id'] = self.__shift_id

        if self['driver'] == MOVEMENT_DUMP_AREA_NAME:
            self['shift_id'] = 1

        elif self['driver'] == RECYCLE_BIN_NAME:
            self['shift_id'] = 2

    @property
    def tour_string(self):
        return self.refresh_tour_string()

    @tour_string.setter
    def tour_string(self, value):
        self.__tour_string = value
        self['tour_string'] = value

    def __build_driver_loc_mov_type_key(self):

        try:
            self['driver_loc_mov_type_key'] = self[
                'dep_date_time'].strftime('%H%M') + '->' + \
                self['tour_loc_string'] + '->' + \
                self['arr_date_time'].strftime('%H%M')

        except Exception:
            log_exception(
                popup=False, remarks='building driver_loc_mov_type_key failed!')

    def refresh_tour_string(self):

        self.__build_driver_loc_mov_type_key()

        self.__tour_string = self['shiftname'] + \
            '|' + self.driver_loc_mov_type_key

        self['tour_string'] = self.__tour_string

        return self.__tour_string

    def set_shift_id(self, value=None):
        self.__shift_id = value
        self['shift_id'] = self.__shift_id

    @property
    def list_movements(self):
        return self.get('list_movements', self.get('list_tour_movements', []))

    @list_movements.setter
    def list_movements(self, x):
        self['list_movements'] = x

    def modify_dep_day(self, wkday='Mon'):

        try:

            if wkday == self.get('weekday', 'Mon'):
                return self['dep_date_time']

            wkdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ndays = wkdays.index(wkday) - \
                wkdays.index(self.get('weekday', 'Mon'))

            _dep_datetime = self['dep_date_time']

            _dep_datetime = _dep_datetime + timedelta(days=ndays)

            return _dep_datetime

        except Exception:
            log_exception(
                popup=True, remarks=f"modify_dep_day Failed!")

        return None

    def refresh(self, target_weekday=''):
        """
        This module will refresh base tour, loaded from Shifts to obtain
        dct_tour for the target_weekday. The module assumes that the base
        shift has weekday key available
        """

        if 'weekday' not in self.keys():
            self['weekday'] = 'Mon'

        if target_weekday == self['weekday']:
            return

        wkdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        try:

            try:

                days_offset = 0

                __d_dep = self['dep_date_time']
                __d_arr = self['arr_date_time']
                __d_shft = self['shift_end_datetime']

                days_offset = wkdays.index(
                    target_weekday) - wkdays.index(self['weekday'])

                __list_m = self.get('list_movements', [])

                self.update({
                    'dep_date_time': __d_dep + timedelta(days=days_offset),
                    'arr_date_time': __d_arr + timedelta(days=days_offset),
                    'shift_end_datetime': __d_shft + timedelta(days=days_offset)
                })

                __dct_running_tour_data = self.pop(
                    'dct_running_tour_data', {})

                __ms = [m for m in set(
                    __dct_running_tour_data) if m in __list_m]

                for m in __ms:
                    __sdt = __dct_running_tour_data.get(
                        m, {}).get('sdatetime', 0)

                    if __sdt:
                        __edt = __dct_running_tour_data.get(
                            m, {}).get('edatetime', 0)

                        if __edt:

                            __dct_running_tour_data[m].update({
                                'sdatetime': __sdt + timedelta(days=days_offset),
                                'edatetime': __edt + timedelta(days=days_offset)
                            })

                self['dct_running_tour_data'] = __dct_running_tour_data

                self['weekday'] = target_weekday

            except Exception:
                log_exception(
                    popup=False,
                    remarks='The tour could not be modified.')

        except Exception:
            log_exception(
                popup=False,
                remarks='The tour could not be modified.')

    def apply_movment_mapping(self, dct_mov_map={}):

        try:

            if dct_mov_map:

                list_movements = self['list_movements']

                list_movements_to_process = [
                    m for m in list_movements if m in dct_mov_map.keys()]

                if list_movements_to_process:

                    self['list_movements'] = [
                        dct_mov_map.get(m, m) for m in list_movements]

                    __dct_break = self.get(
                        'dct_running_tour_data', {})

                    if __dct_break:

                        __set_m = set(__dct_break)
                        self['dct_running_tour_data'] = {
                            dct_mov_map.get(m, m): __dct_break[m] for m in __set_m}

                    __movs = self['list_movements']
                    self['list_loaded_movements'] = [
                        x for x in __movs if IsLoaded(x).is_loaded()]

                    return True

        except Exception:
            log_exception(
                popup=False,
                remarks='Movement mapping failed.')

        return False


if __name__ == '__main__':

    from lion.create_flask_app.create_app import LION_FLASK_APP
    import sys
    with LION_FLASK_APP.app_context():

        dct_tour_sample = {'movement_shift_pair': [(1001930, 5628), (1000909, 5628)],
                           'Source': 'LION',
                           'arr_date_time': Timestamp('2022-10-05 04:05:00'),
                           'avg_utilisation': 0.01,
                           'dct_running_tour_data': {1000909: {'Break': 0,
                                                               'idle_time_after_mov': 202.0,
                                                               'loc': 'ABZ',
                                                               'poa': 0,
                                                               'sdatetime': None,
                                                               'tdt': 380.0,
                                                               'tdtb4brk': 185.0,
                                                               'twt': 710.0,
                                                               'twtb4brk': 425.0},
                                                     1001930: {'Break': 60,
                                                               'edatetime': Timestamp('2022-10-04 21:00:00'),
                                                               'idle_time_after_mov': 255.0,
                                                               'loc': 'GW4',
                                                               'poa': 195.0,
                                                               'remarks': 'The driver can take an hour '
                                                               'break at GW4. ',
                                                               'sdatetime': Timestamp('2022-10-04 20:00:00'),
                                                               'strArrDateTime': '2022-10-04 21:00',
                                                               'strDepDateTime': '2022-10-04 20:00',
                                                               'tdt': 195.0,
                                                               'tdtb4brk': 195.0,
                                                               'twt': 495.0,
                                                               'twtb4brk': 0}},
                           'dep_date_time': Timestamp('2022-10-04 16:15:00'),
                           'double_man': False,
                           'driver': 'ABZ.S2',
                           'driver_loc_mov_type_key': '1615->ABZ->GW4->ABZ->0405',
                           'driving_time': 380.0,
                           'hbr': True,
                           'idle_time': 275.0,
                           'input_driving_time': 370.0,
                           'interim_idle_times': [280],
                           'is_complete': True,
                           'is_feas': True,
                           'is_fixed': False,
                           'list_loaded_movements': [1001930, 1000909],
                           'list_loaded_movements_string': '100672->100638',
                           'list_movements': [1001930, 1000909],
                           'mouseover_info': '',
                           'n_input_movs': 2,
                           'n_repos_movs': 0,
                           'notifications': '',
                           'remark': 'The driver leaves ABZ at 16:45. Then drives for 3 hours and 5 '
                           'minutes to arrive at GW4 at 19:50. The driver can take an hour '
                           'break at GW4. PoA at this location is 3 hours and 15 minutes. '
                           'Finally, drives for 3 hours and 5 minutes to arrive at ABZ at '
                           '03:35. The total shift duration is 11 hours and 5 minutes. The '
                           'total driving time is 6 hours and 20 minutes. ',
                           'repos_driving_time': 0.0,
                           'shift_end_datetime': Timestamp('2022-10-05 04:25:00'),
                           'time_utilisation': 67.88990825688073,
                           'total_dist': 468.0,
                           'total_dist_cost': 234.0,
                           'total_dur': 710.0,
                           'tour_cntry_from': 'GB',
                           'tour_cost': 384.0,
                           'tour_dist': 468.0,
                           'tour_fixed_cost': 150,
                           'tour_id': 5628,
                           'tour_input_dist': 468.0,
                           'tour_loc_from': 'ABZ',
                           'tour_loc_string': 'ABZ->GW4->ABZ',
                           'tour_repos_dist': 0.0,
                           'vehicle': 1,
                           'weekday': 1
                           }

        print(f"Size: {sys.getsizeof(dct_tour_sample)}")
