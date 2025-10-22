from datetime import datetime, date
from lion.logger.exception_logger import log_exception


def get_week_num(tday=datetime.now()):

    try:
        y = tday.year

        wkday = date(y-1, 6, 1).strftime('%a')
        extr_wkn = int(wkday != 'Mon')

        __fiscal_y_start_week = date(y-1, 6, 1).isocalendar().week
        __last_y_dec_week = date(y-1, 12, 31).isocalendar().week

        __wkcnt = __last_y_dec_week - __fiscal_y_start_week + 1

        wk_num = __wkcnt + tday.isocalendar().week
        wk_num = wk_num - 52 - extr_wkn if wk_num > 52 else wk_num - extr_wkn

        return 'WK%s' % (f'000{wk_num}'[-2:])

    except Exception as err:
        log_exception(
            popup=False, remarks=f'Could not generate week number string! {str(err)}')
        return tday.strftime('%Y%m%d')
