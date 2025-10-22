from os import environ, getpid
from pathlib import Path
from time import sleep
import setproctitle

from lion.logger.logger_handler import initialize_logger
from lion.utils.process_pool_manager import ProcessPoolManager
setproctitle.setproctitle(f"py-lion-main:{getpid()}")
sleep(0.5)  # Give time for the process title to update

ProcessPoolManager.get_executor()
initialize_logger()

LION_LOG_FILE_PATH = Path().resolve() / 'status.log'
environ['LION_PKG_MODULES_PATH'] = str(Path(__file__).resolve().parent)
environ['LION_LOG_FILE_PATH'] = str(LION_LOG_FILE_PATH)
