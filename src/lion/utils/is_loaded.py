
from lion.logger.exception_logger import log_exception
from lion.orm.shift_movement_entry import ShiftMovementEntry


class IsLoaded():

    def __init__(self, movement_id=0):

        try:
            self.__movement = int(movement_id)
        except Exception:
            self.__movement = 0
            self.__str_id = movement_id

    @property
    def loaded(self):
        if self.__movement:
            return self.is_loaded(self.__movement)
        else:
            return not self.__str_id.lower().endswith('|empty')

    def is_loaded(self, m=0):
        try:
            return ShiftMovementEntry.is_loaded_movement(m)
        except Exception:
            log_exception(f'IsLoaded.is_loaded failed for movement id {m}')
            return False

    def is_repos(self, m):
        try:
            return not ShiftMovementEntry.is_loaded_movement(m)
        except Exception:
            log_exception(f'IsLoaded.is_repos failed for movement id {m}')
            return False
