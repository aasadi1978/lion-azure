from lion.orm.user_params import UserParams
from lion.ui.basket.basket_shifts import get_basket_shift_ids
from lion.logger.exception_logger import log_exception


def add_shifts_to_my_basket(self, **dct_params):

    try:
        __drivers = dct_params['drivers']
        __get_right_click_id = dct_params['get_right_click_id']

        if not __drivers:
            if __get_right_click_id:
                __drivers = [self._right_click_id]

        if __drivers:

            _str_existing_shifts = get_basket_shift_ids()

            all_shifts= []
            if _str_existing_shifts != '':

                all_shifts= _str_existing_shifts.split('|')
                all_shifts= [int(x) for x in all_shifts if str(x).isnumeric()]

            if all_shifts:
                __drivers = [
                    d for d in __drivers if d not in all_shifts]

            all_shifts.extend(__drivers)

            all_shifts= list(set(all_shifts))

            if all_shifts:
                UserParams.update(basket_shifts='|'.join(str(x) for x in all_shifts))

            all_shifts= [
                int(x) for x in all_shifts]
            
            self._options.update(
                {'basket_drivers': all_shifts})

    except Exception:

        self._pre_load_my_shifts_in_basket()
        log_exception(
            popup=False, remarks='Adding shift to my basket failed.')

    return {'drivers': all_shifts}