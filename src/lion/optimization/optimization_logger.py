from dataclasses import dataclass
from datetime import datetime

from lion.config import paths
from lion.logger.exception_logger import log_exception as exc_logger
from lion.logger.status_logger import log_message as log_status
from lion.utils.singleton_meta import SingletonMeta
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER
from lion.utils.session_manager import SESSION_MANAGER


@dataclass
class OptimizationLogFile(metaclass=SingletonMeta):

    OPT_GLOBAL_ERROR: str = ''
    OPT_GLOBAL_WARNING: str = ''

    def _initialize(self, mode='w'):

        if self._initialized:
            return

        try:
            self._log_file = paths.LION_OPTIMIZATION_LOG_FILE_PATH

            self.OPT_GLOBAL_ERROR = ''
            self.OPT_GLOBAL_WARNING = ''

            message = f"Optimization module log initialised. on {str(datetime.now())[:19]} By: {SESSION_MANAGER.get('user_name')}"

            with open(self._log_file, mode) as f:
                f.write(message)

            log_status(message=message)

            self._initialized = True

        except Exception:
            self._initialized = False
            exc_logger()


    def reset(self):

        self._initialized = False
        self._initialize()

    @classmethod
    def get_instance(cls):
        return cls()

    def log_exception(self, message='', **kwargs):
        """
        Logs an exception message to the log file.
        """

        if 'remarks' in kwargs:
            message = f"{message}. {kwargs['remarks']} " if message else kwargs['remarks']

        msg2log = exc_logger(message=message)

        self.OPT_GLOBAL_ERROR = f"{self.OPT_GLOBAL_ERROR}. {message}" if self.OPT_GLOBAL_ERROR else message
        STATUS_CONTROLLER.PROGRESS_INFO = f"An error has occured: {self.OPT_GLOBAL_ERROR}"

        self.log_info(message=msg2log)

    def log_warnning(self, message='', **kwargs):
        """
        Logs a warrning message to the log file.
        """
        if 'remarks' in kwargs:
            message = f"{message}. {kwargs['remarks']} " if message else kwargs['remarks']

        timestamp = str(datetime.now())[:19]
        msg2log = f"\n{timestamp}|{message}"

        self.OPT_GLOBAL_WARNING = f"{self.OPT_GLOBAL_WARNING}. {message}" if self.OPT_GLOBAL_WARNING else message

        self.log_info(message=msg2log)

    def log_statusbar(self, message):
        if not STATUS_CONTROLLER.PROGRESS_INFO.startswith('An error has occured'):
            STATUS_CONTROLLER.PROGRESS_INFO = f"{message}"

    def log_message(self, message=''):
        self.log_info(message=message)

    def log_info(self, message=''):

        timestamp = str(datetime.now())[:19]
        msg2log = f"\n{timestamp}: {message}"

        try:
            with open(self._log_file, 'a') as f:
                f.writelines(msg2log)
        except Exception as err:
            error_message = f"\n{timestamp}|{str(err)}\n"
            with open(self._log_file, 'a') as f:
                f.writelines(error_message)
            msg2log = error_message

        log_status(message=msg2log)


OPT_LOGGER = OptimizationLogFile.get_instance()