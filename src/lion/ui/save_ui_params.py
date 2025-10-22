from lion.logger.exception_logger import log_exception
from lion.ui.ui_params import UI_PARAMS


def refresh_schedule_filters(**dct_params):
    try:
        UI_PARAMS.LIST_FILTERED_SHIFT_IDS = [int(shid) for shid in dct_params.get('shifts', [])] if dct_params.get('shifts', []) else []
        UI_PARAMS.DICT_DRIVERS_PER_PAGE = {}
        UI_PARAMS.FILTERING_LOC_CODES = dct_params.get('loc_codes', []) if dct_params.get('loc_codes', []) else []
        UI_PARAMS.FILTERING_VEHICLES = [int(vcode) for vcode in dct_params.get('Vehicles', [])] if dct_params.get('Vehicles', []) else []
        UI_PARAMS.PAGE_NUM = 1 if not dct_params.get('page_num', 0) == 1 else dct_params['page_num']

    except Exception:
        log_exception(
            popup=False, remarks=f"Could not refresh_schedule_filters!")