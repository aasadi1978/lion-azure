    
from lion.changeovers.changeover_shifts import get_changeover_shiftids
from lion.orm.drivers_info import DriversInfo
from lion.orm.shift_index import ShiftIndex
from lion.ui.chart import get_chart_data
from lion.ui.ui_params import UI_PARAMS
from lion.logger.exception_logger import log_exception


def chart(list_changeovers=[]):

    try:
        shifts = []

        for lcstr in list_changeovers:
            shifts.extend(get_changeover_shiftids(
                loc_string=lcstr.split('(')[0].strip()))

        _list_filtered_drivers = list(set(shifts))
        page_size = UI_PARAMS.PAGE_SIZE
        UI_PARAMS.PAGE_NUM = 1

        if _list_filtered_drivers:
            _dict_drivers_per_page = ShiftIndex.get_page_shifts(dct_shift_ids=DriversInfo.to_sub_dict(
                shift_ids=_list_filtered_drivers), pagesize=page_size)

            UI_PARAMS.DICT_DRIVERS_PER_PAGE = _dict_drivers_per_page
            UI_PARAMS.LIST_FILTERED_SHIFT_IDS = _list_filtered_drivers

        return get_chart_data(drivers=_list_filtered_drivers, page_num=UI_PARAMS.PAGE_NUM)

    except Exception:
        return {'code': 400, 'error': f'Could not get shifts for changeovers: {log_exception()}'}