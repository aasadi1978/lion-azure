from lion.logger.exception_logger import log_exception
from lion.orm.traffic_type import TrafficType
from lion.ui.ui_params import UI_PARAMS


def refresh_traffic_type_colors() -> None:
    try:
        dct_traffic_type_colors = TrafficType.dict_traffic_type()
    except Exception:
        log_exception('Failed to fetch traffic type colors from the database!')
        dct_traffic_type_colors = {}
    
    UI_PARAMS.update(dct_traffic_type_colors=dct_traffic_type_colors)
