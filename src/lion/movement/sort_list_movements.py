from lion.movement.movements_manager import UI_MOVEMENTS
from lion.shift_data.exceptions import EXCEPTION_HANDLER
from lion.logger.exception_logger import log_exception

def are_movements_overlapped(list_of_movs=[]) -> bool:

    movements_overlapped = False
    list_of_movements_sorted = []
    
    try:

        if not list_of_movs:
            raise KeyError("list_of_movs was empty!")
        
        _misngs = [
            m for m in list_of_movs if m not in UI_MOVEMENTS.dict_all_movements]

        if _misngs:
            raise KeyError(f"Some movements do not exist! {'|'.join([str(x) for x in _misngs])}")

        __dct_dt = {
            m: UI_MOVEMENTS.dict_all_movements[m]['DepDateTime'] for m in list_of_movs}

        __dct_arrt = {
            m: UI_MOVEMENTS.dict_all_movements[m]['ArrDateTime'] for m in list_of_movs}

        __sorted_dt = dict(
            sorted(__dct_dt.items(), key=lambda item: item[1]))

        list_of_movements_sorted = list(__sorted_dt)

        if len(list_of_movements_sorted) > 1:

            nMovs = len(list_of_movements_sorted)
            for i in range(1, nMovs):

                movements_overlapped = (
                    __sorted_dt[list_of_movements_sorted[i]] - __dct_arrt[list_of_movements_sorted[i-1]]).total_seconds() < 300

                if movements_overlapped:
                    return True

    except Exception:
        if list_of_movements_sorted:
            EXCEPTION_HANDLER.update(log_exception(
                    popup=False, remarks='Sorting movements failed!'))
        
    return False


def sorted_movements(list_of_movs=[]):

    time_refresh_required = False
    list_of_movements_sorted = []
    
    try:

        if not list_of_movs:
            raise KeyError("list_of_movs was empty!")
        
        _misngs = [
            m for m in list_of_movs if m not in UI_MOVEMENTS.dict_all_movements]

        if _misngs:
            raise KeyError(f"Some movements do not exist! {'|'.join([str(x) for x in _misngs])}")

        __dct_dt = {
            m: UI_MOVEMENTS.dict_all_movements[m]['DepDateTime'] for m in list_of_movs}

        __dct_arrt = {
            m: UI_MOVEMENTS.dict_all_movements[m]['ArrDateTime'] for m in list_of_movs}

        __sorted_dt = dict(
            sorted(__dct_dt.items(), key=lambda item: item[1]))

        list_of_movements_sorted = list(__sorted_dt)

        if len(list_of_movements_sorted) > 1:

            nMovs = len(list_of_movements_sorted)
            for i in range(1, nMovs):

                time_refresh_required = (
                    __sorted_dt[list_of_movements_sorted[i]] - __dct_arrt[list_of_movements_sorted[i-1]]).total_seconds() < 1500

                if time_refresh_required:
                    break

    except Exception:
        if list_of_movements_sorted:
            EXCEPTION_HANDLER.update(log_exception(
                    popup=False, remarks='Sorting movements failed!'))
        
        return [], False

    return list_of_movements_sorted, time_refresh_required