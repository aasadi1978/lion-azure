from lion.orm.user_params import UserParams
from lion.ui.options import refresh_options
from lion.logger.exception_logger import log_exception


def empty_basket():
    try:
        UserParams.update(param='basket_shifts', val='')
        refresh_options({'basket_drivers':[]})
        return {'drivers': []}
    except Exception:
        log_exception(popup=False)