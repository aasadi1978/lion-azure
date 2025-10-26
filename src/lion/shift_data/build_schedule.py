from datetime import datetime
import logging
from lion.changeovers.validate_changeovers_data import validate_changeovers
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.orm.drivers_info import DriversInfo
from lion.movement.dct_movement import DictMovement
from datetime import datetime, timedelta
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.shift_data.process_driver_info_record import transform_shift_record
from lion.bootstrap.constants import LION_DATES, MOVEMENT_DUMP_AREA_NAME, RECYCLE_BIN_NAME
from lion.orm.location import Location
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.ui.ui_params import UI_PARAMS
from lion.utils import safe_copy
from lion.utils.popup_notifier import show_error
from lion.logger.exception_logger import log_exception


"""
Assumes that data copied to local tables: shifts, local_movements
"""

class BuildSchedule():

    def __init__(self):

        try:

            logging.info("Initializing BuildSchedule module ...")
            UI_MOVEMENTS.reset()
            UI_SHIFT_DATA.reset()

            self._dct_footprint = Location.to_dict()
            self.__dct_m_shift_id = {}
            self.__processed_shifts = []

        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}")

    def load_baseline_shift_data(self) -> tuple[dict, dict] | None:
        """
        This module loads the entire baseline, i.e., full week schedule and movs stored in local_schedule database
        """

        self.__processed_shifts = []
        _dct_baseline_schedule = {}
        _dct_baseline_movements = {}

        try:

            logging.info(f"Loading baseline shift data ...")

            baseline_status = self.__build_baseline()
            if baseline_status:
                _dct_baseline_schedule, self.__dct_m_shift_id = baseline_status
                _dct_baseline_movements = self._build_baseline_movements()

                if _dct_baseline_schedule and (len(self.__processed_shifts) < len(_dct_baseline_schedule)):

                        logging.warning(f"Some shifts have no associated movements and will be removed from the schedule!")
                        _dct_baseline_schedule = {k: v for k, v in _dct_baseline_schedule.items() 
                                                        if k in self.__processed_shifts}

                        _dct_baseline_schedule = safe_copy.secure_copy(_dct_baseline_schedule)
            
            else:
                logging.error(f'Building baseline schedule failed!')
                return None

        except Exception as e:
            logging.error(f'Loading baseline shift data failed: {str(e)}')
            _dct_baseline_schedule = {}
            _dct_baseline_movements = {}
            return None


        if not _dct_baseline_schedule or not _dct_baseline_movements:
            UI_SHIFT_DATA.optimal_drivers = {}
            UI_MOVEMENTS.dict_all_movements = {}
            logging.error(f'No baseline schedule or movements data found!')
            return None

        else:
            try:
                UI_SHIFT_DATA.optimal_drivers = _dct_baseline_schedule
                UI_MOVEMENTS.dict_all_movements = _dct_baseline_movements
                UI_SHIFT_DATA.refresh_dct_shift_ids_per_loc_page()
                validate_changeovers()
            except Exception as e:
                logging.error(f'Loading baseline shift data failed: {str(e)}')
                UI_SHIFT_DATA.optimal_drivers = {}
                UI_MOVEMENTS.dict_all_movements = {}

                return None

        return _dct_baseline_schedule, _dct_baseline_movements

    def __build_baseline(self) -> tuple[dict, dict] | None:

        _dct_baseline_schedule = {}
        _dct_m_shift_id = {}
        logging.info("Building baseline schedule ...")

        try:
            # Update supplier info before processing
            DriversInfo.update_suppliers()
            scn_shift_ids_records = DriversInfo.get_all_valid_records()

            transformed_shift_data_list = []
            for rec in scn_shift_ids_records:
                try:
                    result = transform_shift_record(rec)
                    if result:
                        transformed_shift_data_list.append(result)
                except Exception as e:
                    logging.error(f"Error transforming shift record {rec}: {e}")

            for shift_info_tuple in transformed_shift_data_list:
                if not shift_info_tuple:
                    continue
                shift_id, dct_base_schedule, dct_m_shift = shift_info_tuple
                _dct_baseline_schedule[shift_id] = dct_base_schedule
                _dct_m_shift_id.update(dct_m_shift)

        except Exception as e:
            logging.exception(f"Error while building baseline schedule: {e}")
            return None

        if not _dct_baseline_schedule or not _dct_m_shift_id:
            logging.warning("Baseline schedule or shift mapping is empty — returning None.")
            return None

        return _dct_baseline_schedule, _dct_m_shift_id


    # def __build_baseline_multiprocessing(self) -> tuple[dict, dict] | None:
    #     from lion.utils.process_pool_manager import ProcessPoolManager
    #     from concurrent.futures.process import BrokenProcessPool
    #     _dct_baseline_schedule = {}
    #     _dct_m_shift_id = {}
    #     logging.info("Building baseline schedule ...")

    #     try:
    #         DriversInfo.update_suppliers()
    #         scn_shift_ids_records = DriversInfo.get_all_valid_records()
    #         executor = ProcessPoolManager.get_executor()

    #         try:
    #             transformed_shift_data_list = list(
    #                 executor.map(transform_shift_record, scn_shift_ids_records)
    #             )
    #         except BrokenProcessPool:
    #             # Automatically restart pool and retry once
    #             ProcessPoolManager.restart_executor()
    #             executor = ProcessPoolManager.get_executor()
    #             transformed_shift_data_list = list(
    #                 executor.map(transform_shift_record, scn_shift_ids_records)
    #             )
    #         except Exception as e:
    #             logging.error(f"Error during multiprocessing shifts info: {str(e)}")
    #             return None

    #         for shift_info_tuple in transformed_shift_data_list:
    #             if shift_info_tuple:
    #                 shift_id, dct_base_schedule, dct_m_shift = shift_info_tuple
    #                 _dct_baseline_schedule[shift_id] = dct_base_schedule
    #                 _dct_m_shift_id.update(dct_m_shift)

    #     except Exception as e:
    #         logging.error(f"Multiprocessing shifts info failed: {str(e)}")
    #         return None

    #     if not _dct_baseline_schedule or not _dct_m_shift_id:
    #         return None

    #     return _dct_baseline_schedule, _dct_m_shift_id


    def _build_baseline_movements(self) -> dict | None:

        _dct_baseline_movements = {}
        base_week_day = 'Mon'
        logging.info("Building baseline movements ...")


        try:

            all_mov_records: list[ShiftMovementEntry] = ShiftMovementEntry.all_movement_objects()

            dct_shift_names = DriversInfo.dct_shiftnames(shift_ids=[
                mobj.shift_id for mobj in all_mov_records if mobj.shift_id > 0])
            
            dct_shift_names.update(
                {1: MOVEMENT_DUMP_AREA_NAME, 2: RECYCLE_BIN_NAME, 0: 'NotScheduled'})

        except Exception as e:
            logging.error(f"Reading movements failed: {str(e)}")
            return None
        
        if not all_mov_records:
            return None

        all_mov_records_unplanned=[mobj.movement_id for mobj in all_mov_records if mobj.shift_id in [0]]

        for movObj in all_mov_records:

            try:

                origin, dest, depday, deptime, vehicle, traffic_type = movObj.str_id.split(
                    '|')

                vehicle = int(vehicle)
                depday = int(depday)
                mov_id = movObj.movement_id
                is_repos = traffic_type.lower() == 'empty'

                shift_id = 0 if (all_mov_records_unplanned and (mov_id in all_mov_records_unplanned)) else  \
                    self.validate_shift_id(movObj)

                if shift_id in [1, 2]:
                    continue

                if shift_id in dct_shift_names:
                    shiftname = dct_shift_names[shift_id]
                else:
                    shiftname = DriversInfo.get_shift_name(
                        shift_id=shift_id)

                driving_time, dist = UI_RUNTIMES_MILEAGES.retrieve_travel_time_and_distance(
                    orig=origin, dest=dest, vehicle=vehicle)

                loc_string = movObj.loc_string
                tu_dest = movObj.tu_dest or ''
                is_changeover = ShiftMovementEntry.is_changeover(
                    loc_string=loc_string)

                locs = []

                if is_changeover and tu_dest == '':

                    locs = loc_string.split('.')
                    locs.pop()
                    tu_dest = locs.pop()
                else:
                    loc_string = ''

                dct_m = {}

                dct_m['weekday'] = base_week_day
                DepDateTime = self.__get_datetime(
                    depday=depday, deptime=deptime, schedule_day=base_week_day)

                if not DepDateTime:
                    raise ValueError(
                        'Dep date time cannot be None!')

                if driving_time is None:
                    raise ValueError('Driving time was None!')

                dct_m['DepDateTime'] = DepDateTime
                dct_m['ArrDateTime'] = DepDateTime + timedelta(
                    minutes=driving_time)

                dct_m['MovementID'] = mov_id
                dct_m['From'] = origin
                dct_m['To'] = dest
                dct_m['VehicleType'] = vehicle
                dct_m['TrafficType'] = traffic_type
                dct_m['tu'] = tu_dest
                dct_m['loc_string'] = loc_string

                dct_m['shift'] = shiftname

                dct_m['shift_id'] = shift_id

                dct_m['draggableX'] = False if is_repos else True
                dct_m['draggableY'] = dct_m['draggableX']
                dct_m['is_repos'] = is_repos

                dct_m['DrivingTime'] = driving_time

                dct_m['Utilisation'] = 0.01
                dct_m['PayWeight'] = 0
                dct_m['Pieces'] = 0
                dct_m['Capacity'] = 18000

                dct_m['Dist'] = dist

                dct_m['CountryFrom'] = UI_PARAMS.LION_REGION,

                dct_m['last_update'] = datetime.now().strftime(
                    '%Y-%m-%d %H%M')

                dct_m = DictMovement(**dct_m)
                dct_m.update_str_id()

            except Exception:
                dct_m = {}
                log_exception(f"Error when building the movement {origin}->{dest}->{traffic_type}-(vhType: {vehicle})")

            if dct_m:
                self.__processed_shifts.append(shift_id)
                _dct_baseline_movements[mov_id] = dct_m

        if not _dct_baseline_movements:
            return None
        
        return _dct_baseline_movements

    def __get_datetime(self, depday, deptime, schedule_day='Mon'):

        try:
            time_obj = datetime.strptime(
                f'0000{deptime}'[-4:], "%H%M").time()
            dep_date_time = datetime.combine(
                LION_DATES[schedule_day], time_obj)

            dep_date_time = dep_date_time + timedelta(days=depday)

            return dep_date_time

        except Exception as e:
            show_error(f"date time could not be built: {str(e)}")

        return None

    def validate_shift_id(self, movObj: ShiftMovementEntry):

        try:
            shift_id = movObj.shift_id
            mov_id = movObj.movement_id
            shift_id_scheduled = self.__dct_m_shift_id.get(mov_id, None)
                        
            if shift_id_scheduled is None:
                if movObj.shift_id:
                    shift_id_scheduled = movObj.shift_id
                else:
                    raise ValueError(
                                    f"The movements id {mov_id} is labeled as planned but does not have associated shiftid!")

            if shift_id_scheduled and shift_id_scheduled != movObj.shift_id:
                ShiftMovementEntry.update_movement_shift_ids(dct_movement_shift_id={mov_id: shift_id_scheduled})
                shift_id = int(shift_id_scheduled)

            return shift_id
        
        except Exception as e:
            logging.error(f"validate_shift_id failed for movement id {mov_id}: {str(e)}")
            return 2
