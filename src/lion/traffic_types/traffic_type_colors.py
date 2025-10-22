import logging
from lion.orm.traffic_type import TrafficType
from lion.traffic_types.update_traffic_types import update_traffic_types
from lion.ui.ui_params import UI_PARAMS
from lion.logger.exception_logger import log_exception


def refresh_traffic_type_colors() -> None:

    try:
        update_traffic_types()
    except Exception:
        log_exception(popup=False)

    try:
        dct_traffic_type_colors = TrafficType.dict_traffic_type()
    except Exception:
        logging.error('Failed to fetch traffic type colors from the database!')
        dct_traffic_type_colors = {}
    
    UI_PARAMS.update(dct_traffic_type_colors=dct_traffic_type_colors)
