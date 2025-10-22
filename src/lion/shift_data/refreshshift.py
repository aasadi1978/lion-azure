from lion.logger.status_logger import log_message
from lion.shift_data.save import SaveSchedule
from lion.shift_data.shift_manager import SHIFT_MANAGER
from lion.ui.chart import get_chart_data
from lion.ui.ui_params import UI_PARAMS
from lion.logger.exception_logger import log_exception

def evaluate_shift(shift_id):

    if not shift_id:
        return False
    
    status_ok = False

    try:

        if SHIFT_MANAGER.refresh_shift_after_drag(
                new_m=None,
                shift_id=shift_id):

            _notifications = SHIFT_MANAGER.notifications

            if _notifications != '':
                log_message(f"{_notifications}")

            if not SaveSchedule(impacted_shifts=[shift_id]).save_ok:
                raise ValueError(f'Save schedule failed when evaluating {shift_id}!')

            status_ok = True

    except Exception:
        status_ok = False
        log_exception(popup=False, remarks=f'Evaluation failed!')

    return status_ok

def refresh_shift(**dct_params):

    _pagenum = dct_params.get('pagenum', '')
    shift_id = dct_params.get('shift_id', 0)

    right_click_id = UI_PARAMS.RIGHT_CLICK_ID

    if right_click_id:
        UI_PARAMS.RIGHT_CLICK_ID=0

    shift_id = right_click_id if right_click_id > 0 else shift_id
    _notifications = ''

    try:

        if not shift_id:
            raise Exception('No shift_id was provide!')

        if SHIFT_MANAGER.refresh_shift_after_drag(
                new_m=None,
                shift_id=shift_id):

            _notifications = SHIFT_MANAGER.notifications

            if not SaveSchedule(impacted_shifts=[shift_id]).save_ok:
                raise ValueError(f'Save schedule failed when refreshing {shift_id}!')

    except Exception:

        err = log_exception(popup=False, remarks=f'Refreshing failed!')
        return {'code': 400, 'error': f"{err}. {_notifications}", 'notifications':''}


    return {'code': 200, 'chart_data': get_chart_data(page_num=_pagenum), 'notifications': _notifications}
