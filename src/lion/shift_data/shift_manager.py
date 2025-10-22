from datetime import timedelta
from lion.config.paths import LION_LOGS_PATH
from lion.movement.dct_movement import DictMovement
from lion.movement import sort_list_movements
from lion.shift_data import refresh_movement_timings
from lion.shift_data.notifications import NOTIFICATION_HANDLER
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.tour.tour_analysis import UI_TOUR_ANALYSIS
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.ui.ui_params import UI_PARAMS
from lion.logger.exception_logger import log_exception
from lion.orm.drivers_info import DriversInfo
from lion.orm.vehicle_type import VehicleType
from lion.orm.location import Location
from lion.utils.minutes2hhmm_str import minutes2hhmm_str
from lion.shift_data.exceptions import EXCEPTION_HANDLER
from lion.shift_data.build_tours import build as _build_tours
from lion.utils.safe_copy import secure_copy


class ShiftManager():

    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        pass

    def __init_app(self):

        try:
            NOTIFICATION_HANDLER.reset()
            EXCEPTION_HANDLER.reset()
            self.__dict_all_movements = UI_MOVEMENTS.dict_all_movements

        except Exception:
            log_exception(
                popup=True, remarks='RepairShift could not be initialised!')
    
    def reset(self):
        self.__init_app()
    
    @classmethod
    def get_instance(cls):
        return cls()

    @property
    def exception_message(self):
        msg = EXCEPTION_HANDLER.get()
        EXCEPTION_HANDLER.reset()
        return msg

    @exception_message.setter
    def exception_message(self, x):
        EXCEPTION_HANDLER.reset()
        EXCEPTION_HANDLER.update(x)

    @property
    def notifications(self):

        notifcation = NOTIFICATION_HANDLER.get()
        NOTIFICATION_HANDLER.reset()

        return notifcation

    @notifications.setter
    def notifications(self, x):
        NOTIFICATION_HANDLER.reset()
        NOTIFICATION_HANDLER.update(x)
    
    def _refresh_movements_data(self, dct_movement_changes={}):

        try:
            if not self.__dict_all_movements:
                raise Exception('dict_all_movements is empty!')
                
            if dct_movement_changes:

                self.__dict_all_movements.update({m: DictMovement(**dct_movement_changes[m]) 
                                                  for m in dct_movement_changes.keys()})

                UI_MOVEMENTS.dict_all_movements = self.__dict_all_movements

        except Exception:
            log_exception(popup=False, remarks='Refreshing movements failed!')


    def refresh_shift_after_drag(self,
                                 new_m=None,
                                 dct_time_changed_movements={},
                                 removed_movements=set(),
                                 shift_id=0):

        try:

            self.__dict_all_movements = UI_MOVEMENTS.dict_all_movements
            self.__dct_drivers = DriversInfo.to_dict()
            self.__dct_footprint = Location.to_dict()
            list_of_processed_movements = []

            list_of_shift_movements = UI_SHIFT_DATA.optimal_drivers[shift_id].list_movements
            shift_vehicle = UI_SHIFT_DATA.optimal_drivers[shift_id].get('vehicle', 1)
            shiftname = self.__dct_drivers[shift_id]['shiftname']

            if new_m:

                shift_vehicle = self._validate_vehicle(new_m, shift_vehicle, shiftname)

                if not shift_vehicle:
                    return False
                
                list_of_shift_movements.append(new_m)

            list_of_shift_movements, dct_movs_before_change = self._refresh_shift_movements(
                dct_time_changed_movements=secure_copy(dct_time_changed_movements), 
                removed_movements=secure_copy(removed_movements), 
                list_of_shift_movements=secure_copy(list_of_shift_movements))

            if not list_of_shift_movements:
                return UI_SHIFT_DATA.blank_shift(shift_id=shift_id)

            list_of_shift_movements, time_refresh_required = sort_list_movements.sorted_movements(
                list_of_movs=secure_copy(list_of_shift_movements))

            vehicle = self.__dct_drivers[shift_id]['vehicle']
            _is_doubleman = DriversInfo.is_doubleman(shift_id=shift_id)
            is_driver_home_base = self.__dct_drivers.get(shift_id, {}).get('hbr', True)

            UI_PARAMS.SHIFT_INFO=';'.join(
                [str(is_driver_home_base), str(_is_doubleman), str(vehicle)])

            UI_MOVEMENTS.vehicle = shift_vehicle

            list_of_processed_movements.extend(list_of_shift_movements)

            if time_refresh_required:
                refresh_movement_timings.refresh(list_movements=secure_copy(list_of_processed_movements))
                
            __dct_tour = {}
            __dct_tour = _build_tours(shift_id=shift_id,
                                           list_of_sorted_loaded_movements=secure_copy(list_of_processed_movements),
                                           is_doubleman= _is_doubleman)
            if not __dct_tour:

                __driver_loc = self.__dct_drivers.get(
                    shift_id, {}).get('start position', '')

                if __driver_loc == '':
                    raise ValueError(
                        f'No start position was found for the shift {shift_id}: shift_id is known: {shift_id in self.__dct_drivers}')

                while list_of_shift_movements:

                    m1 = list_of_shift_movements.pop(0)
                    if list_of_shift_movements:

                        m2 = list_of_shift_movements[0]

                        if self.__dict_all_movements[m1]['To'] != \
                                self.__dict_all_movements[m2]['From']:

                            __new_m = UI_MOVEMENTS.insert_intermediate_m(
                                m1=m1, m2=m2)

                            if __new_m:
                                list_of_processed_movements.insert(
                                    list_of_processed_movements.index(m1) + 1, __new_m)

                                refresh_movement_timings.refresh(
                                    list_movements=list_of_processed_movements
                                )

                del list_of_shift_movements

                if __driver_loc != self.__dict_all_movements[list_of_processed_movements[0]]['From']:

                    turnaround_non_drive = self.__dct_footprint[
                        self.__dict_all_movements[list_of_processed_movements[0]]['From']]['chgover_non_driving_min']

                    turnaround_drive = self.__dct_footprint[
                        self.__dict_all_movements[list_of_processed_movements[0]]['From']]['chgover_driving_min']

                    __dct_m = UI_MOVEMENTS.get_dct_arriving_movement(
                        orig=__driver_loc,
                        dest=self.__dict_all_movements[list_of_processed_movements[0]]['From'],
                        ArrDateTime=self.__dict_all_movements[
                            list_of_processed_movements[0]]['DepDateTime'] - timedelta(minutes=turnaround_non_drive + turnaround_drive)
                    )

                    list_of_processed_movements.insert(
                        0, __dct_m['MovementID'])

                if is_driver_home_base and (
                        __driver_loc != self.__dict_all_movements[list_of_processed_movements[-1]]['To']):

                    turnaround_non_drive = self.__dct_footprint[
                        self.__dict_all_movements[list_of_processed_movements[-1]]['To']]['chgover_non_driving_min']

                    turnaround_drive = self.__dct_footprint[
                        self.__dict_all_movements[list_of_processed_movements[-1]]['To']]['chgover_driving_min']

                    __dct_m = UI_MOVEMENTS.get_dct_departing_movement(
                        dest=__driver_loc,
                        orig=self.__dict_all_movements[list_of_processed_movements[-1]]['To'],
                        DepDateTime=self.__dict_all_movements[
                            list_of_processed_movements[-1]]['ArrDateTime'] + timedelta(minutes=turnaround_non_drive + turnaround_drive)
                    )

                    if __dct_m:
                        list_of_processed_movements.append(
                            __dct_m['MovementID'])

                __dct_tour_break_data_per_m = UI_TOUR_ANALYSIS.process_tour(
                    list_movements=list_of_processed_movements,
                    double_man=_is_doubleman,
                    vehicle=shift_vehicle)

                for m, v in __dct_tour_break_data_per_m.items():

                    __m_is_repos_and_first_movement = list_of_processed_movements.index(
                        m) == 0 and self.__dict_all_movements[m].is_repos()

                    __m2 = list_of_processed_movements[
                        list_of_processed_movements.index(m) + 1]

                    turnaround_non_drive = self.__dct_footprint[
                        self.__dict_all_movements[m]['To']]['chgover_non_driving_min']

                    turnaround_drive = self.__dct_footprint[
                        self.__dict_all_movements[m]['To']]['chgover_driving_min']

                    __turnaroundtime = turnaround_drive + turnaround_non_drive

                    __dlta_minutes = int((self.__dict_all_movements[__m2]['DepDateTime'] -
                                          self.__dict_all_movements[m]['ArrDateTime']).total_seconds()/60 + 0.5)

                    # __turnaroundtime = 0
                    if __dlta_minutes < __turnaroundtime + v['Break']:

                        if __m_is_repos_and_first_movement:
                            __new_dt = self.__dict_all_movements[m]['DepDateTime'] - timedelta(
                                minutes=__turnaroundtime + v['Break'])

                            UI_MOVEMENTS.update_movement_for_new_deptime(
                                m, __new_dt)

                        else:
                            __new_dt = self.__dict_all_movements[m]['ArrDateTime'] + timedelta(
                                minutes=__turnaroundtime + v['Break'])

                            UI_MOVEMENTS.update_movement_for_new_deptime(
                                __m2, __new_dt)

                        refresh_movement_timings.refresh(
                                    list_movements=list_of_processed_movements)

                __status, __remark, __dct_tour = UI_TOUR_ANALYSIS.refresh_tour(
                    shift_id=shift_id,
                    tour_movement_string='->'.join([str(x)
                                                    for x in list_of_processed_movements]),
                    ignore_status=True,
                    ignore_duration=True,
                    double_man=_is_doubleman,
                    vehicle=shift_vehicle
                )

                if __dct_tour:

                    __dct_tour.update(
                        {'vehicle': shift_vehicle, 'shift_id': shift_id})

                    __dct_tour.shiftname = shiftname

                    __dct_tour = UI_TOUR_ANALYSIS.calculate_cost(
                        __dct_tour)

            if __dct_tour:

                __remarks = ''
                for m in set(dct_movs_before_change):

                    __loc_to = '.'.join([
                        self.__dict_all_movements[m]['From'],
                        self.__dict_all_movements[m]['To']])

                    __delay = int(0.5 + (self.__dict_all_movements[m][
                        'DepDateTime'] - dct_movs_before_change[m]).total_seconds()/60)

                    if __delay > 0:
                        __remarks = __remarks + \
                            '%s\n' % ('%s delayed by %s. ' %
                                      (__loc_to, minutes2hhmm_str(__delay)))

                __infeas_remarks = __dct_tour.get('notifications', '')
                if __remarks != '':

                    if __infeas_remarks != '':
                        __infeas_remarks = '%s \n%s' % (
                            __infeas_remarks, __remarks)
                    else:
                        __infeas_remarks = '%s' % __remarks

                    __dct_tour.update({'notifications': __infeas_remarks})

                if __infeas_remarks != '':
                    NOTIFICATION_HANDLER.update(__infeas_remarks)
                
            else:
                raise ValueError('No feasible shift could be built.')

        except Exception:
            EXCEPTION_HANDLER.update(log_exception(popup=False))
            return False

        try:

            list_of_shift_movements = __dct_tour['list_movements']

            for m in list_of_shift_movements:

                self.__dict_all_movements[m].update(
                    **{'VehicleType': shift_vehicle, 'shift_id': shift_id})

            __dct_tour.refresh_tour_string()

            UI_SHIFT_DATA.update(dct_opt_drivers={shift_id: __dct_tour})

            return True

        except Exception:
            EXCEPTION_HANDLER.update(log_exception(popup=False))
            return False

    def _validate_vehicle(self, movement_id, shift_vehicle, shiftname):

        try:
            movement_vehicle = self.__dict_all_movements[movement_id].get('VehicleType', 0)

            if movement_vehicle > 0 and (shift_vehicle != movement_vehicle):
                m_vehicle = VehicleType.get_vehicle_short_name(movement_vehicle)
                shift_vehicle = VehicleType.get_vehicle_short_name(
                            shift_vehicle)

                raise ValueError(
                            f'The selected {m_vehicle} movement cannot be assigned ' +
                            f'to the {shift_vehicle} shift {shiftname}!')
                    
            return shift_vehicle

        except Exception:
            EXCEPTION_HANDLER.update(log_exception(popup=False))
            return 0

    def _refresh_shift_movements(self, **kwargs):

        dct_time_changed_movements = kwargs.get('dct_time_changed_movements', {})
        removed_movements = kwargs.get('removed_movements', set())
        list_of_shift_movements = kwargs.get('list_of_shift_movements', [])

        dct_movs_before_change = {}

        try:

            if removed_movements:
                list_of_shift_movements = [m for m in list_of_shift_movements if m not in removed_movements]


            if dct_time_changed_movements:

                dct_movs_before_change.update({m: self.__dict_all_movements[m]['DepDateTime'] for m in list_of_shift_movements})

                self._refresh_movements_data(dct_movement_changes=dct_time_changed_movements)

                if dct_time_changed_movements:
                    list_of_shift_movements = [m for m in list_of_shift_movements if (
                        m in dct_time_changed_movements.keys() or self.__dict_all_movements[m].is_loaded())]

            else:
                list_of_shift_movements = [m for m in list_of_shift_movements if self.__dict_all_movements[m].is_loaded()]
                dct_movs_before_change.update({m: self.__dict_all_movements[m]['DepDateTime'] for m in list_of_shift_movements})

            return list_of_shift_movements, dct_movs_before_change

        except Exception:
            EXCEPTION_HANDLER.update(log_exception(popup=False))
            return [], {}


    def review_shifts(self):

        set_shift_ids = set()
        shift_refresh_logs = set()
        infeas_log_file = LION_LOGS_PATH / 'infeasible-shifts.log'

        with open(infeas_log_file, 'w'):
            pass

        shift_ids = list(UI_SHIFT_DATA.optimal_drivers.keys())
 
        for shift_id in shift_ids:

            if shift_id in [1, 2]:
                continue

            try:
                refreshed = self.refresh_shift_after_drag(
                    new_m=None,
                    shift_id=shift_id
                )

                if not refreshed:

                    shiftname = UI_SHIFT_DATA.optimal_drivers[shift_id].shiftname
                    shift_refresh_logs.update([shiftname])
                    set_shift_ids.update([shift_id])

                    with open(infeas_log_file, 'a') as f:
                        f.write(f'Shift {shiftname} could not be rebuilt successfully.\n')

            except Exception:

                set_shift_ids.update([shift_id])
                shift_refresh_logs.update([shiftname])
                with open(infeas_log_file, 'a') as f:
                    f.write(f'Shift {shiftname} could not be rebuilt successfully: {log_exception()}\n')

        if shift_refresh_logs:
            return {'code': 400, 
                    'message': f'{len(shift_refresh_logs)} shifts could not be rebuilt successfully.\nSee {infeas_log_file}'}

        return {'code': 200, 'message': 'Shifts refreshed successfully!'}

SHIFT_MANAGER = ShiftManager.get_instance()