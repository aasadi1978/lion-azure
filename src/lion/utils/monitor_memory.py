

from psutil import virtual_memory
from lion.logger.exception_logger import log_exception
from lion.ui.ui_params import UI_PARAMS


def monitor_memory_usage():
    try:
        memory_info = virtual_memory()
        UI_PARAMS.MEMORY_USAGE = memory_info.percent
    except Exception:
        log_exception(popup=False, remarks='Getting memory usage failed!')
        UI_PARAMS.MEMORY_USAGE = None