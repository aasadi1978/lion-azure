from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.orm.drivers_info import DriversInfo
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.ui.ui_params import UI_PARAMS
from lion.logger.exception_logger import log_exception


class SaveSchedule():

    def __init__(self, impacted_movements=[], impacted_shifts=[]):

        self.__impacted_shifts = list(UI_PARAMS.SET_IMPACTED_SHIFTS) if not impacted_shifts else impacted_shifts
        self.__impacted_movements = impacted_movements
        self.__save_status = ''

        self.__save_changes()

    @property
    def save_status(self):
        return self.__save_status

    @property
    def save_ok(self):
        return self.__save_status == ''

    def __save_changes(self):
        """
        Saves changes on a local copies of Shifts and Movements: Shifts and LocalMovements classes
        """

        try:

            if not self.__impacted_shifts and not self.__impacted_movements:
                return

            if self.__impacted_shifts:

                try:
                    dct_impacted_shifts = {d: UI_SHIFT_DATA.optimal_drivers[d]
                                           for d in self.__impacted_shifts}
                except Exception:
                    dct_impacted_shifts = {}
                    self.__save_status = f"{self.__save_status}{
                        log_exception(popup=False)}. "

                # Then save them on the loacal shifts table
                # Note dct_tours is of type DctTour
                # The updated shift data will be saved under version 0 with a new timestamp

                if not dct_impacted_shifts:
                    return

                for shift_id in dct_impacted_shifts:

                    dct_optimal_driver = dct_impacted_shifts[shift_id]
                    _movements_imported = True
                    _dct_imapcted_movs = {}

                    if dct_optimal_driver:

                        try:

                            _shift_movs = dct_impacted_shifts[shift_id].list_movements

                            _dct_imapcted_movs = {
                                m: UI_SHIFT_DATA.dict_all_movements[m] for m in _shift_movs}

                        except Exception:
                            _movements_imported = False
                            _dct_imapcted_movs = {}
                            self.__save_status = f"{self.__save_status}{
                                log_exception(popup=False)}. "

                        if _dct_imapcted_movs:

                            for m in _shift_movs:

                                _dct_m = _dct_imapcted_movs[m]
                                _dct_m.update_str_id()

                                if not ShiftMovementEntry.update_movement_info(dct_m=_dct_m):
                                    """
                                    First try to update existing movement info but if the movment is new
                                    then we attempt to add it to the database. I tis key to insert running days
                                    for adding a  new mov
                                    """

                                    if not ShiftMovementEntry.add_dct_m(dct_m=_dct_m):

                                        _movements_imported = False
                                        raise ValueError(
                                            'add_dct_m was not successful on LocalMovements. ')

                    if _movements_imported and dct_optimal_driver:

                        if not DriversInfo.save_dct_tours(dct_tours={shift_id: dct_optimal_driver}):
                            raise ValueError(
                                f'save_dct_tours was not successful on LocalDriversInfo for {shift_id}. ')

            elif self.__impacted_movements:

                try:
                    _dct_imapcted_movs = {
                        m: UI_SHIFT_DATA.dict_all_movements[m] for m in self.__impacted_movements}

                except Exception:
                    _dct_imapcted_movs = {}
                    self.__save_status += f"{log_exception(popup=False)}. "

                if _dct_imapcted_movs:

                    for m in _dct_imapcted_movs.keys():

                        if _dct_imapcted_movs.get(m, {}):

                            _dct_imapcted_movs[m].update_str_id()

                            if not ShiftMovementEntry.update_movement_info(
                                    dct_m=_dct_imapcted_movs[m]):

                                """
                                    First try to update existing movement info but if the public is new
                                    then we attempt to add it to the database. I tis key to insert running days
                                    for adding a  new mov
                                    """

                                if not ShiftMovementEntry.add_dct_m(
                                        dct_m=_dct_imapcted_movs[m]):

                                    raise ValueError(
                                        'add_dct_m was not successful on LocalMovements. ')

        except Exception:
            self.__save_status = f"{self.__save_status}{
                log_exception(popup=False)}. "
