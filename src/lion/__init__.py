from os import environ, getpid
from pathlib import Path

import setproctitle
from lion.logger.logger_handler import initialize_logger
setproctitle.setproctitle(f"py-lion-main:{getpid()}")

initialize_logger()
LION_PROJECT_HOME = Path(str(Path().resolve())).resolve()

LION_LOG_FILE_PATH = LION_PROJECT_HOME / 'status.log'
environ['LION_PKG_MODULES_PATH'] = str(Path(__file__).resolve().parent)
environ['LION_LOG_FILE_PATH'] = str(LION_LOG_FILE_PATH)
environ['LION_PROJECT_HOME'] = str(LION_PROJECT_HOME)
