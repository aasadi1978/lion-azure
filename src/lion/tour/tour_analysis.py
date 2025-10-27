from datetime import timedelta
from collections import defaultdict
import logging

from lion.movement.movements_manager import UI_MOVEMENTS
from lion.logger.exception_logger import log_exception
from lion.tour.dct_tour import DctTour
from lion.ui.ui_params import UI_PARAMS
from lion.utils.minutes2hhmm_str import minutes2hhmm_str
from lion.utils.is_loaded import IsLoaded
from lion.tour.cost import TourCost
from lion.orm.location import Location
from lion.orm.drivers_info import DriversInfo


class TourAnalysis():

    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self):
        pass
        
    
    def initialize(self):

        if not self._initialized:
            try:
                self.__is_loaded = IsLoaded()
                self.__tour_cost = TourCost()
                self.__dct_drivers = DriversInfo.to_dict()
                self.__dct_footprint = Location.to_dict()

                self._reset_tour_parameters()
                self._initialized = True

            except Exception:
                log_exception(
                    popup=False, remarks='TourAnalysis could not be initialised!')
    
    def reset(self):
        self._initialized = False
        self.initialize()
    
    @classmethod
    def get_instance(cls):
        return cls()

    @property
    def status_report(self):
        return self.__status_report

    def _reset_tour_parameters(self):

        try:

            self.__time_margin_min = 5

            self.__double_man_shift_dur = UI_PARAMS.DOUBLE_MAN_SHIFT_DUR

            self.__maxtourdur_start = UI_PARAMS.MAX_TOUR_DUR
            self.__maxdrivingtime_start = UI_PARAMS.MAX_DRIVING_DUR + self.__time_margin_min

            self.__maxdrivingtime = int(self.__maxdrivingtime_start)
            self.__maxtourdur = int(self.__maxtourdur_start)

            self.__drivingtimeb4break = UI_PARAMS.DRIVING_TIME_B4_BREAK + self.__time_margin_min
            self.__driving_time_break = UI_PARAMS.MIN_BREAK_TIME
            self.__workingtimeb4break = UI_PARAMS.WORKING_TIME_B4_BREAK + self.__time_margin_min
            self.__working_time_break = UI_PARAMS.MIN_BREAK_TIME_WORKING


        except Exception:
            log_exception(
                popup=False, remarks='Refrshing network params failed!')

    def calculate_cost(self, dct_tour):
        return self.__tour_cost.calculate_cost(dct_tour=dct_tour)

    def refresh_tour(self,
                     shift_id=0,
                     tour_movement_string='',
                     ignore_status=False,
                     ignore_duration=False,
                     capture_infeas_remarks=False,
                     double_man=False,
                     vehicle=1):

        try:
            
            self._reset_tour_parameters()
            self.__capture_infeas_remarks = capture_infeas_remarks
            self.__status_report = ''
            self.__shift_overall_break = 0
            self.__shift_overall_idle_time = 0

            __maxtourdur = self.__maxtourdur_start * 1
            __maxdrivingtime = self.__maxdrivingtime_start * 1

            # self.__dct_movements = dct_movements
            self.__dct_movements = UI_MOVEMENTS.dict_all_movements

            self.__latest_driving_time_break = self.__driving_time_break * 1
            __2nd_break_time = self.__driving_time_break - 15

            ignore_break = int(double_man or (int(vehicle) == 4))
            calc_break = int(not ignore_break)

            if ignore_break:

                self.__latest_driving_time_break = 0
                self.__working_time_break = 0
                __2nd_break_time = 0

            self.__maxtourdur = self.__double_man_shift_dur if double_man else self.__maxtourdur_start
            self.__maxdrivingtime = self.__double_man_shift_dur if double_man else self.__maxdrivingtime_start

            if not double_man and (ignore_break or ignore_duration or ignore_status):

                self.__maxdrivingtime = int(2 * self.__maxdrivingtime_start)
                self.__maxtourdur = int(2 * self.__maxtourdur_start)

            __status_code = 1
            list_movements = [int(x)
                              for x in tour_movement_string.split('->')]

            __list_tour_movements_with_breaks = []
            __list_tour_movements_with_breaks.extend(list_movements)

            self.__list_tour_movements = list_movements

            __loaded_movements = [
                m for m in self.__list_tour_movements if self.__is_loaded.is_loaded(m)]

            if not __loaded_movements:
                return 0, 'No loaded movement.', {}

            __n_input_movs = len(__loaded_movements)
            __n_repos_movs = len(self.__list_tour_movements) - __n_input_movs

            __locs = [self.__dct_movements[m]['From']
                      for m in self.__list_tour_movements]
            __locs.append(
                self.__dct_movements[self.__list_tour_movements[-1]]['To'])

            __debrief_time_at_orig = self.__dct_footprint[__locs[0]
                                                          ]['dep_debrief_time']

            self.__debrief_time_at_dest = self.__dct_footprint[__locs[-1]
                                                               ]['dep_debrief_time']

            self.__latest_recom_stime_based_on_wrktime = self.__dct_movements[self.__list_tour_movements[0]]['DepDateTime'] - timedelta(
                minutes=__debrief_time_at_orig) + timedelta(minutes=self.__workingtimeb4break)

            __driving_time = 0
            __idle_time = 0
            __total_dur = __debrief_time_at_orig * 1

            i = 0

            __initial_remark = f'The driver leaves {__locs[0]} at {
                self.__dct_movements[self.__list_tour_movements[0]]['DepDateTime'].strftime("%H:%M")}. '

            __idle_time_list = []

            __break_status_OK = True
            __tour_is_ok_sofar = len(self.__list_tour_movements) <= 1
            __driving_time_b4_break = 0
            __working_time_b4_break = __debrief_time_at_orig * 1

            __m_pairs = [(self.__list_tour_movements[i], self.__list_tour_movements[i+1])
                         for i in range(len(self.__list_tour_movements)-1)]

            self.__dct_tour_break_data_per_loc = defaultdict(dict)
            __dct_remarks = defaultdict(str)

            while __m_pairs:

                __m1, __m2 = __m_pairs.pop(0)
                __gap_btwn_m1_m2 = int((self.__dct_movements[__m2]['DepDateTime'] -
                                        self.__dct_movements[__m1]['ArrDateTime']).total_seconds()/60)

                __turnaround_drive = self.__dct_footprint[self.__dct_movements[__m1]
                                                          ['To']]['chgover_driving_min']
                __turnaround_non_drive = self.__dct_footprint[self.__dct_movements[__m1]
                                                              ['To']]['chgover_non_driving_min']

                __m1_driving_time = self.__dct_movements[__m1]['DrivingTime']
                __driving_time += (__m1_driving_time + __turnaround_drive)

                __driving_time_b4_break += (__m1_driving_time +
                                            __turnaround_drive) * calc_break

                __working_time_b4_break += (__m1_driving_time +
                                            __turnaround_drive) * calc_break

                __remark = 'Then drives for %s to arrive at %s at %s. ' % (
                    minutes2hhmm_str(
                        __m1_driving_time), self.__dct_movements[__m1]['To'],
                    self.__dct_movements[__m1]['ArrDateTime'].strftime("%H:%M"))

                __is_driving_time_ok = __driving_time <= self.__maxdrivingtime
                __idle_time_list.append(__gap_btwn_m1_m2)

                __total_dur += (__m1_driving_time + __gap_btwn_m1_m2)
                __dur_is_ok = __total_dur <= self.__maxtourdur

                __idle_time_after_mov = max(0, (__gap_btwn_m1_m2 -
                                                __turnaround_drive - __turnaround_non_drive))

                __dct_remarks[__m1] = __dct_remarks[__m1] + __remark

                __idle_time += __idle_time_after_mov

                # and __break_status_OK and __is_mov_dur_ok
                __tour_is_ok_sofar = __dur_is_ok and __is_driving_time_ok

                self.__dct_tour_break_data_per_loc[__m1].update({
                    'tdt': __driving_time,
                    'twt': __total_dur,
                    'twtb4brk': __working_time_b4_break,
                    'tdtb4brk': __driving_time_b4_break,
                    'poa': __idle_time_after_mov,
                    'Break': 0,
                    'edatetime': self.__dct_movements[__m2]['DepDateTime'] - timedelta(
                        minutes=__turnaround_non_drive),
                    'sdatetime': self.__dct_movements[__m1]['ArrDateTime'] + timedelta(
                        minutes=__turnaround_drive),
                    'edt_init': self.__dct_movements[__m2]['DepDateTime'] - timedelta(
                        minutes=__turnaround_non_drive),
                    'sdt_init': self.__dct_movements[__m1]['ArrDateTime'] + timedelta(
                        minutes=__turnaround_drive),
                    'idle_time_after_mov': __idle_time_after_mov,
                    'loc': self.__dct_movements[__m1]['To']
                })

                __working_time_b4_break += (__turnaround_non_drive +
                                            __idle_time_after_mov)

                if not __tour_is_ok_sofar:
                    if not ignore_status:
                        self.__update_status_report(
                            f'DrivingTime: {__driving_time}; total_dur: {__total_dur}')
                        break

                i += 1

            ######################################################################
            if __tour_is_ok_sofar or ignore_status:

                __last_movement = self.__list_tour_movements[-1]

                __m_driving_time = self.__dct_movements[__last_movement]['DrivingTime']
                __driving_time += __m_driving_time
                __total_dur += (__m_driving_time + self.__debrief_time_at_dest)

                __driving_time_b4_break += __m_driving_time
                __working_time_b4_break += (
                    __m_driving_time + self.__debrief_time_at_dest)

                self.__dct_tour_break_data_per_loc[__last_movement].update({
                    'tdt': __driving_time,
                    'twt': __total_dur,
                    'twtb4brk': __working_time_b4_break,
                    'tdtb4brk': __driving_time_b4_break,
                    'poa': max(0, self.__maxtourdur - __total_dur),
                    'Break': 0,
                    'sdatetime': None,
                    'edatetime': None,
                    'idle_time_after_mov': max(0, self.__maxtourdur - __total_dur),
                    'loc': self.__dct_movements[__last_movement]['To']

                })

                __dct_remarks[__last_movement] = __dct_remarks[
                    __last_movement] + 'Finally, drives for %s to arrive at %s at %s. ' % (
                    minutes2hhmm_str(
                        __m_driving_time), self.__dct_movements[__last_movement]['To'],
                    self.__dct_movements[__last_movement]['ArrDateTime'].strftime("%H:%M"))

                __is_driving_time_ok = __driving_time <= self.__maxdrivingtime
                __dur_is_ok = __total_dur <= self.__maxtourdur

                __tour_is_ok_sofar = __tour_is_ok_sofar and __dur_is_ok and __is_driving_time_ok

            #############
            #############

            if __tour_is_ok_sofar or ignore_status:

                for m1 in self.__list_tour_movements:

                    tdtb4brk = self.__dct_tour_break_data_per_loc[m1]['tdtb4brk']
                    twtb4brk = self.__dct_tour_break_data_per_loc[m1]['twtb4brk']

                    __brkdur = self.__latest_driving_time_break if tdtb4brk > self.__drivingtimeb4break else (
                        self.__working_time_break if twtb4brk > self.__workingtimeb4break else 0
                    )

                    if __brkdur:

                        __m1_idx = self.__list_tour_movements.index(m1)
                        __list_movs_with_break_option = [
                            m11 for m11 in self.__list_tour_movements if self.__dct_tour_break_data_per_loc[
                                m11].get('idle_time_after_mov', 0) >= __brkdur]

                        __list_movs_with_break_option = [m for m in __list_movs_with_break_option if self.__list_tour_movements.index(
                            m) < __m1_idx and self.__dct_tour_break_data_per_loc[m]['Break'] <= self.__working_time_break]

                        if __list_movs_with_break_option:

                            __mm = __list_movs_with_break_option.pop()
                            __brk_used = self.__dct_tour_break_data_per_loc[__mm]['Break']

                            self.__refresh_dct_running_tour_data(break_m=__mm,
                                                                 break_dur=__brkdur, assigned_brk=__brk_used)

                            twtb4brk2 = self.__dct_tour_break_data_per_loc[m1]['twtb4brk']
                            tdtb4brk2 = self.__dct_tour_break_data_per_loc[m1]['tdtb4brk']

                            __brkdur2 = self.__latest_driving_time_break if tdtb4brk2 > self.__drivingtimeb4break else (
                                self.__working_time_break if twtb4brk2 > self.__workingtimeb4break else 0
                            )

                            __break_status_OK = (__brkdur2 == 0)

                        else:
                            __break_status_OK = False

                        if not __break_status_OK:
                            break

                        if __brkdur == self.__latest_driving_time_break:
                            self.__latest_driving_time_break = __2nd_break_time

                if __break_status_OK:

                    twtb4brk = self.__dct_tour_break_data_per_loc[m1]['twtb4brk']
                    tdtb4brk = self.__dct_tour_break_data_per_loc[m1]['tdtb4brk']

                    __brkdur = self.__latest_driving_time_break if tdtb4brk > self.__drivingtimeb4break else (
                        self.__working_time_break if twtb4brk > self.__workingtimeb4break else 0
                    )

                    __break_status_OK = (__brkdur == 0)

                __break_status_OK = \
                    __break_status_OK or double_man or (
                        self.__latest_driving_time_break == 0)

                __tour_is_ok_sofar = __tour_is_ok_sofar and __break_status_OK

                self.__update_status_report(
                    f'DrivingTime: {__driving_time}; total_dur: {__total_dur}; break_status_OK: {__break_status_OK}')
            else:
                self.__update_status_report(
                    f'DrivingTime: {__driving_time}; total_dur: {__total_dur}')
            ######################################################################

            __input_driving_time = sum(
                self.__dct_movements[m]['DrivingTime'] for m in __loaded_movements)

            __last_m = self.__list_tour_movements[-1]

            for m in self.__list_tour_movements:  # [:-1]

                __brk_time = self.__dct_tour_break_data_per_loc.get(
                    m, {}).get('Break', 0)

                self.__shift_overall_break += __brk_time

                if __brk_time > 0:
                    __dct_remarks[m] = __dct_remarks[m] + \
                        self.__dct_tour_break_data_per_loc[m]['remarks']

                __poa = self.__dct_tour_break_data_per_loc.get(
                    m, {}).get('poa', 0)

                self.__dct_tour_break_data_per_loc[m].update(
                    {'poa': __poa - __brk_time})

                if __poa - __brk_time > 0 and m != __last_m:

                    self.__shift_overall_idle_time += (__poa - __brk_time)

                    __dct_remarks[m] = __dct_remarks[m] + \
                        'PoA at this location is %s. ' % (
                            minutes2hhmm_str(__poa - __brk_time))

            __remark = __initial_remark
            __remark_infeas = ''
            for m in self.__list_tour_movements:
                __remark = __remark + __dct_remarks[m]

            if __dur_is_ok:
                __remark = __remark + \
                    'The total shift duration is %s. ' % (
                        minutes2hhmm_str(__total_dur))

            if __total_dur > __maxtourdur:
                __remark_infeas = __remark_infeas + 'Too long shift: %s. ' % (
                    minutes2hhmm_str(__total_dur))

            if __is_driving_time_ok:
                __remark = __remark + \
                    'The total driving time is %s. ' % (
                        minutes2hhmm_str(__driving_time))
            else:
                __remark_infeas = __remark_infeas + \
                    'Too long DT: %s. ' % (
                        minutes2hhmm_str(__driving_time))

            if __driving_time > __maxdrivingtime:
                __remark_infeas = __remark_infeas + \
                    'Too long DT: %s. ' % (
                        minutes2hhmm_str(__driving_time))

            if not __break_status_OK:
                __remark_infeas = __remark_infeas + \
                    'Not enough break time!'

            if __remark_infeas != '':
                __remark = 'INFEASIBLE: %s\n%s' % (__remark_infeas, __remark)
                self.__update_status_report(
                    f'Summary: {__remark_infeas}')

            if double_man:
                __remark = f'{__remark}. The shift is double-man!'

            __status_code = int(__tour_is_ok_sofar)

            if self.__maxtourdur > __maxtourdur:
                if __total_dur > __maxtourdur:
                    self.__maxtourdur = __total_dur * 1
                else:
                    self.__maxtourdur = __maxtourdur * 1

            dct_tour = {}
            __status_code = __status_code and (__total_dur is not None)

            if __status_code == 1 or ignore_status:

                dct_tour.update({'list_movements': list_movements})
                dct_tour.update(
                    {'shift_id': shift_id,
                     'driver': self.__dct_drivers.get(shift_id, {}).get('shiftname', 'Unknown')
                     })
                dct_tour.update({'list_loaded_movements': __loaded_movements})

                dct_tour.update({'movement_shift_pair': [(m, shift_id)
                                                         for m in __loaded_movements]})

                __dep_date_time = self.__dct_movements[self.__list_tour_movements[0]
                                                       ]['DepDateTime'] - timedelta(minutes=__debrief_time_at_orig)
                __arr_date_time = self.__dct_movements[self.__list_tour_movements[-1]
                                                       ]['ArrDateTime'] + timedelta(minutes=self.__debrief_time_at_dest)

                __shift_end_datetime = __dep_date_time + \
                    timedelta(minutes=self.__maxtourdur)

                # __idle_time += max(0, self.__maxtourdur - __total_dur)
                self.__shift_overall_idle_time += max(
                    0, self.__maxtourdur - __total_dur)

                dct_tour.update({
                    'dep_date_time': __dep_date_time,
                    'arr_date_time': __arr_date_time,
                    'shift_end_datetime': __shift_end_datetime,
                    'tour_cntry_from': UI_PARAMS.LION_REGION,
                    'is_complete': (__locs[0] == __locs[-1]),
                    'tour_loc_from': self.__dct_movements[self.__list_tour_movements[0]]['From'],
                    'tour_loc_string': '->'.join(__locs),
                    'total_dur': __total_dur,
                    'tour_repos_dist': sum(self.__dct_movements[m]['Dist'] * self.__dct_movements[m]['is_repos'] for m in self.__list_tour_movements),
                    'tour_input_dist': sum(self.__dct_movements[m]['Dist'] for m in __loaded_movements),
                    'driving_time': __driving_time,
                    'input_driving_time': __input_driving_time,
                    'repos_driving_time': sum(self.__dct_movements[m]['DrivingTime'] * self.__dct_movements[m]['is_repos'] for m in self.__list_tour_movements),
                    'idle_time': int(self.__shift_overall_idle_time),
                    'break_time': int(self.__shift_overall_break),
                    'is_feas': (__status_code == 1),
                    'is_fixed': False,
                    'Source': 'LION',
                    'dct_running_tour_data': dict(self.__dct_tour_break_data_per_loc),
                    'remark': __remark,
                    'notifications': __remark_infeas,
                    'mouseover_info': '',
                    'avg_utilisation': 0.01,
                    'time_utilisation': __input_driving_time * 100/self.__maxdrivingtime,
                    'n_repos_movs': __n_repos_movs,
                    'n_input_movs': __n_input_movs,
                    # 'vehicle': __vehicle,
                    'interim_idle_times': __idle_time_list,
                    # 'weekday': 1,  # 1 for Monday ... 5 for Friday
                    'double_man': double_man
                })

                dct_tour['driver_loc_mov_type_key'] = dct_tour[
                    'dep_date_time'].strftime('%H%M') + '->' + \
                    dct_tour['tour_loc_string'] + '->' + \
                    dct_tour['arr_date_time'].strftime('%H%M')

            return __status_code, __remark, DctTour(**dct_tour)

        except Exception:
            message = log_exception(popup=False)
            __remark = '%s;%s' % (__remark, message)

            return -5, __remark, {}

    def process_tour(self,
                     list_movements=[],
                     dct_movements={},
                     double_man=False,
                     vehicle=1):

        self._reset_tour_parameters()
        self.__latest_driving_time_break = self.__driving_time_break * 1
        __2nd_break_time = self.__driving_time_break - 15

        dct_movements = UI_MOVEMENTS.dict_all_movements if not dct_movements else dct_movements

        if double_man or (int(vehicle) == 4):

            self.__latest_driving_time_break = 0
            self.__working_time_break = 0
            __2nd_break_time = 0

        __list_tour_movements_with_breaks = []
        __list_tour_movements_with_breaks.extend(list_movements)

        try:
            self.__list_tour_movements = []
            self.__list_tour_movements.extend(list_movements)

            __loaded_movements = [
                m for m in self.__list_tour_movements if self.__is_loaded.is_loaded(m)]

            if not __loaded_movements:
                return 0, 'No loaded movement.', {}

            __locs = [dct_movements[m]['From']
                      for m in self.__list_tour_movements]
            __locs.append(dct_movements[self.__list_tour_movements[-1]]['To'])

            __debrief_time = self.__dct_footprint[__locs[-1]
                                                  ]['arr_debrief_time'] * int(__locs[0] == __locs[-1])
            __driving_time = 0
            __total_dur = __debrief_time * 1

            __driving_time_b4_break = 0
            __working_time_b4_break = __debrief_time * 1

            __m_pairs = [(self.__list_tour_movements[i], self.__list_tour_movements[i+1])
                         for i in range(len(self.__list_tour_movements)-1)]

            self.__dct_tour_break_data_per_loc = defaultdict(dict)

            while __m_pairs:

                __m1, __m2 = __m_pairs.pop(0)
                __gap_btwn_m1_m2 = (dct_movements[__m2]['DepDateTime'] -
                                    dct_movements[__m1]['ArrDateTime']).total_seconds()/60

                __turnaround_drive = self.__dct_footprint[dct_movements[__m1]
                                                          ['To']]['chgover_driving_min']

                __turnaround_non_drive = self.__dct_footprint[dct_movements[__m1]
                                                              ['To']]['chgover_non_driving_min']

                __m1_driving_time = dct_movements[__m1]['DrivingTime']
                __driving_time += (__m1_driving_time + __turnaround_drive)

                __driving_time_b4_break += (__m1_driving_time +
                                            __turnaround_drive)

                __working_time_b4_break += (__m1_driving_time +
                                            __turnaround_drive)

                __total_dur += (__m1_driving_time + __gap_btwn_m1_m2)

                __idle_time_after_mov = max(0, (__gap_btwn_m1_m2 -
                                                __turnaround_drive - __turnaround_non_drive))

                self.__dct_tour_break_data_per_loc[__m1].update({
                    'twtb4brk': __working_time_b4_break,
                    'tdtb4brk': __driving_time_b4_break,
                    'idle_time_after_mov': __idle_time_after_mov,
                    'Break': 0,
                    'sdatetime': dct_movements[__m1]['ArrDateTime'] + timedelta(
                        minutes=__turnaround_drive)
                })

                __working_time_b4_break += (__turnaround_non_drive +
                                            __idle_time_after_mov)

            __last_movement = self.__list_tour_movements[-1]

            __m_driving_time = dct_movements[__last_movement]['DrivingTime']
            __driving_time += __m_driving_time
            __total_dur += (__m_driving_time + __debrief_time)

            __driving_time_b4_break += __m_driving_time
            __working_time_b4_break += (
                __m_driving_time + __debrief_time)

            self.__dct_tour_break_data_per_loc[__last_movement].update({
                'twtb4brk': __working_time_b4_break,
                'tdtb4brk': __driving_time_b4_break,
                # max(0, self.__maxtourdur - __total_dur)
                'idle_time_after_mov': 0,
                'Break': 0,
                'sdatetime': None
            })

            #####################
            #######################

            for m1 in self.__list_tour_movements:

                twtb4brk = self.__dct_tour_break_data_per_loc[m1]['twtb4brk']
                tdtb4brk = self.__dct_tour_break_data_per_loc[m1]['tdtb4brk']

                __brkdur = self.__latest_driving_time_break if tdtb4brk > self.__drivingtimeb4break else (
                    self.__working_time_break if twtb4brk > self.__workingtimeb4break else 0
                )

                if __brkdur:

                    __m1_idx = self.__list_tour_movements.index(m1)
                    __list_movs_with_break_option = [
                        m11 for m11 in self.__list_tour_movements if self.__dct_tour_break_data_per_loc[
                            m11]['idle_time_after_mov'] >= __brkdur]

                    __tmp_candid_movs1 = [m for m in __list_movs_with_break_option if self.__list_tour_movements.index(
                        m) < __m1_idx and self.__dct_tour_break_data_per_loc[m]['Break'] <= self.__working_time_break]

                    __tmp_candid_movs2 = []
                    # If __tmp_candid_movs1 is non-empty, this means that there are locations where there is enough time for te required break
                    # and allocated break is either zero or 30 min for working time break. The reason for this is to replace working time
                    # break by a driving time break if required
                    if __tmp_candid_movs1:

                        __mm = __tmp_candid_movs1.pop()
                        __brk_used = self.__dct_tour_break_data_per_loc[__mm]['Break']

                        self.__refresh_dct_running_tour_data_process_tours(break_m=__mm,
                                                                           break_dur=__brkdur, assigned_brk=__brk_used)

                    else:
                        __list_movs_with_break_option_30 = [
                            m11 for m11 in self.__list_tour_movements if self.__dct_tour_break_data_per_loc[
                                m11]['idle_time_after_mov'] >= 30]

                        __tmp_candid_movs2 = [m for m in __list_movs_with_break_option_30 if self.__list_tour_movements.index(
                            m) < __m1_idx and self.__dct_tour_break_data_per_loc[m]['Break'] <= self.__working_time_break]

                        if __tmp_candid_movs2:

                            __mm = __tmp_candid_movs2.pop()
                            __brk_used = self.__dct_tour_break_data_per_loc[__mm]['Break']

                            self.__dct_tour_break_data_per_loc[__mm].update(
                                {'idle_time_after_mov': __brkdur})

                            self.__refresh_dct_running_tour_data_process_tours(break_m=__mm,
                                                                               break_dur=__brkdur,
                                                                               assigned_brk=__brk_used)

                        else:
                            __previous_m = self.__list_tour_movements[self.__list_tour_movements.index(
                                m1) - 1]
                            self.__dct_tour_break_data_per_loc[__previous_m].update(
                                {'idle_time_after_mov': __brkdur})

                            self.__refresh_dct_running_tour_data_process_tours(break_m=__previous_m,
                                                                               break_dur=__brkdur, assigned_brk=0)

                    if __brkdur == self.__latest_driving_time_break:
                        self.__latest_driving_time_break = __2nd_break_time

            return {m: v for m, v in self.__dct_tour_break_data_per_loc.items()
                    if v['Break'] > 0}

        except Exception:
            log_exception(False)

    def __refresh_dct_running_tour_data_process_tours(self, break_m, break_dur, assigned_brk):
        """
        break_m: is the movement being evaluation to assign break after arrival
        break_dur: Is the break time, 60 min, 45 min or 30 min, to assign after this movement
        assigned_brk: Is the break time already assigned due to working time break. If there is
        enough time for driving time break, we delete the 30 min break and replace it by driving time
        break as the driving time break cancels the working time break
        """

        if self.__latest_driving_time_break:

            try:
                __next_movements = [m for m in self.__list_tour_movements if self.__list_tour_movements.index(
                    m) > self.__list_tour_movements.index(break_m)]

                __sdatetime = self.__dct_tour_break_data_per_loc[break_m]['sdatetime']

                self.__dct_tour_break_data_per_loc[break_m].update(
                    {'Break': break_dur,
                        'edatetime': __sdatetime + timedelta(minutes=break_dur)})

                for mov in __next_movements:

                    __mov_twtb4brk = self.__dct_tour_break_data_per_loc[mov]['twtb4brk']
                    __break_m_twtb4brk = self.__dct_tour_break_data_per_loc[break_m]['twtb4brk']

                    if assigned_brk:
                        __mov_twtb4brk_recalculated = __mov_twtb4brk - \
                            (break_dur - assigned_brk)
                    else:
                        __mov_twtb4brk_recalculated = __mov_twtb4brk - __break_m_twtb4brk - break_dur

                    self.__dct_tour_break_data_per_loc[mov].update({
                        'twtb4brk': __mov_twtb4brk_recalculated})

                    if break_dur == self.__latest_driving_time_break:

                        __tdtb4brk = self.__dct_tour_break_data_per_loc[mov]['tdtb4brk']
                        self.__dct_tour_break_data_per_loc[mov].update({'tdtb4brk': __tdtb4brk -
                                                                        self.__dct_tour_break_data_per_loc[
                                                                            break_m]['tdtb4brk']})

                self.__dct_tour_break_data_per_loc[break_m].update({
                    'twtb4brk': 0})

            except Exception:
                log_exception(False)

    def __refresh_dct_running_tour_data(self, break_m, break_dur, assigned_brk):

        try:

            __rmrks = 'The driver can take %s break at %s. ' % (
                minutes2hhmm_str(break_dur), self.__dct_tour_break_data_per_loc[break_m]['loc'])

            if assigned_brk:

                self.__latest_recom_stime_based_on_wrktime - \
                    timedelta(minutes=assigned_brk)

                __turnaround_drive = self.__dct_footprint[self.__dct_movements[break_m]
                                                          ['To']]['chgover_driving_min']

                __break_m_edt_init = self.__dct_tour_break_data_per_loc[break_m]['edt_init']
                __break_m_sdt_init = self.__dct_tour_break_data_per_loc[break_m]['sdt_init']
                self.__dct_tour_break_data_per_loc[break_m].update({'Break': 0,
                                                                    'sdatetime': __break_m_sdt_init,
                                                                    'edatetime': __break_m_edt_init,
                                                                    'remarks': __rmrks
                                                                    })

            #############################################
            __break_m_e_time = self.__dct_tour_break_data_per_loc[break_m]['edatetime']
            __latest_recom_etime_based_on_recom_stime = self.__latest_recom_stime_based_on_wrktime + \
                timedelta(minutes=break_dur)

            if __break_m_e_time <= __latest_recom_etime_based_on_recom_stime:

                self.__dct_tour_break_data_per_loc[break_m].update(
                    {'Break': break_dur,
                        'sdatetime': __break_m_e_time - timedelta(minutes=break_dur),
                        'edatetime': __break_m_e_time,
                        'remarks': __rmrks})

                __latest_break_edatetime = __break_m_e_time

            else:
                __sdate = __latest_recom_etime_based_on_recom_stime - \
                    timedelta(minutes=break_dur)

                __latest_break_edatetime = __latest_recom_etime_based_on_recom_stime

                _dlta_min = self.__dct_footprint[self.__dct_movements[break_m]
                                                 ['To']]['chgover_driving_min']

                if __sdate <= self.__dct_movements[break_m]['ArrDateTime'] + timedelta(minutes=_dlta_min):

                    __sdate = self.__dct_tour_break_data_per_loc[break_m]['sdatetime']
                    __latest_break_edatetime = __sdate + \
                        timedelta(minutes=break_dur)

                self.__dct_tour_break_data_per_loc[break_m].update(
                    {'Break': break_dur,
                        # 'sdatetime': self.__latest_recom_etime - timedelta(minutes=break_dur),
                        'sdatetime': __sdate,
                        # 'edatetime': self.__latest_recom_etime,
                        'edatetime': __latest_break_edatetime,
                        'remarks': __rmrks})

            self.__latest_recom_stime_based_on_wrktime = __latest_break_edatetime + \
                timedelta(minutes=self.__workingtimeb4break)

            __brkm_idx = self.__list_tour_movements.index(break_m)
            __next_movements = [m for m in self.__list_tour_movements if self.__list_tour_movements.index(
                m) > __brkm_idx]

            for mov in __next_movements:

                __turnaround_drive = self.__dct_footprint[self.__dct_movements[mov]
                                                          ['To']]['chgover_driving_min'] + \
                    self.__debrief_time_at_dest * \
                    (mov == self.__list_tour_movements[-1])

                __twtb4brk = int(((self.__dct_movements[mov]['ArrDateTime'] + timedelta(
                    # + (break_dur - assigned_brk) +
                    minutes=__turnaround_drive)) - __latest_break_edatetime).total_seconds()/60)

                self.__dct_tour_break_data_per_loc[mov].update({
                    'twtb4brk': __twtb4brk})

                if break_dur == self.__latest_driving_time_break:

                    __tdtb4brk = self.__dct_tour_break_data_per_loc[mov]['tdtb4brk']
                    self.__dct_tour_break_data_per_loc[mov].update({'tdtb4brk': __tdtb4brk -
                                                                    self.__dct_tour_break_data_per_loc[break_m]['tdtb4brk']})

        except Exception:
            log_exception(False)

    def __update_status_report(self, msg=''):
        if self.__capture_infeas_remarks:
            self.__status_report = f'{self.__status_report}\n{msg}'


UI_TOUR_ANALYSIS = TourAnalysis.get_instance()