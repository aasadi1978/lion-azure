from lion.orm.user_params import UserParams
from lion.logger.exception_logger import log_exception
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.ui.options import refresh_options


def get_basket_shift_ids():
    """
    Returns a list of shifts currently in the user's basket.
    """

    try:
        # Retrieve the existing shifts from lion.user parameters
        _str_existing_shifts = str(UserParams.get_param(param='basket_shifts', if_null=''))
        all_shifts = _str_existing_shifts.split('|') if _str_existing_shifts else []

        if all_shifts:

            all_shifts = [int(x) for x in all_shifts if str(x).isnumeric()]
            all_shifts = [x for x in all_shifts if x in UI_SHIFT_DATA.optimal_drivers.keys()]

        UserParams.update(param='basket_shifts', value='|'.join(map(str, all_shifts)))
        return all_shifts
        
    except Exception as e:
        log_exception(popup=False, remarks=f'Error retrieving shifts in basket: {e}')
    
    return []
