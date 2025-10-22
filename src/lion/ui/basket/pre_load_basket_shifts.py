from lion.orm.user_params import UserParams
from lion.shift_data.shift_data import UI_SHIFT_DATA


def pre_load_my_shifts_in_basket():

    try:
        all_shifts = UserParams.get_param(param='basket_shifts', if_null='')
        all_shifts = all_shifts.split('|') if all_shifts else []

        all_shifts = [int(x) for x in all_shifts if int(x) 
                      in UI_SHIFT_DATA.optimal_drivers.keys()]

    except Exception:
        all_shifts = []

    return all_shifts