from os import environ, getenv, getpid
from pathlib import Path
from time import sleep
import setproctitle

from lion.logger.logger_handler import initialize_logger
from lion.utils.process_pool_manager import ProcessPoolManager
setproctitle.setproctitle(f"py-lion-main:{getpid()}")
sleep(0.5)  # Give time for the process title to update

ProcessPoolManager.get_executor()
initialize_logger()
LION_PROJECT_HOME = Path(getenv('LION_PROJECT_HOME', str(Path().resolve()))).resolve()

LION_LOG_FILE_PATH = LION_PROJECT_HOME / 'status.log'
environ['LION_PKG_MODULES_PATH'] = str(Path(__file__).resolve().parent)
environ['LION_LOG_FILE_PATH'] = str(LION_LOG_FILE_PATH)
environ['LION_PROJECT_HOME'] = str(LION_PROJECT_HOME)