from lion.orm.drivers_info import DriversInfo
from lion.orm.shift_index import ShiftIndex
from lion.ui.basket.basket_shifts import get_basket_shift_ids
from lion.ui.chart import get_chart_data
from lion.ui.ui_params import UI_PARAMS
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.logger.exception_logger import return_exception_code


def chart():
    try:

        _list_filtered_drivers = []

        my_shifts_in_basket = get_basket_shift_ids()

        if not my_shifts_in_basket:
             return get_chart_data()

        my_shifts_in_basket = [x for x in my_shifts_in_basket
                                        if x in UI_SHIFT_DATA.optimal_drivers.keys()]

        _list_filtered_drivers.extend(
            [x for x in my_shifts_in_basket if x not in _list_filtered_drivers])

        _dict_drivers_per_page = ShiftIndex.get_page_shifts(dct_shift_ids=DriversInfo.to_sub_dict(
            shift_ids=_list_filtered_drivers), pagesize=UI_PARAMS.PAGE_SIZE)

        UI_PARAMS.LIST_FILTERED_SHIFT_IDS= _list_filtered_drivers
        UI_PARAMS.DICT_DRIVERS_PER_PAGE = _dict_drivers_per_page
        UI_PARAMS.PAGE_NUM = 1

        return get_chart_data(drivers=_list_filtered_drivers, page_num=UI_PARAMS.PAGE_NUM)

    except Exception:
        return return_exception_code(popup=False, 
                                     remarks="Could not get shifts for changeovers")
