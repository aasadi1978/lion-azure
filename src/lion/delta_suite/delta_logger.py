from dataclasses import dataclass
from datetime import datetime
import logging

from dataclasses import dataclass
from lion.logger.status_logger import log_message as log_status
from pandas import DataFrame
from lion.utils.singleton_meta import SingletonMeta
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER
from lion.logger.exception_logger import log_exception as exc_logger


@dataclass
class DeltaLogFile(metaclass=SingletonMeta):

    DELTA_GLOBAL_ERROR: str = ''
    DELTA_GLOBAL_WARNING: str = ''
    DELTA_DB_CON_STR: str = ''
    DF_MOVEMENTS = DataFrame()
    DF_MOVEMENTS_EXCLUDED_FROM_OPT = DataFrame()

    def __init__(self):
        pass

    def _initialize(self, mode='w'):

        if self._initialized:
            return
        
        try:
            self.DELTA_GLOBAL_ERROR: str = ''
            self.DELTA_GLOBAL_WARNING: str = ''
            self.DELTA_DB_CON_STR: str = ''
            self.DF_MOVEMENTS = DataFrame()
            self.DF_MOVEMENTS_EXCLUDED_FROM_OPT = DataFrame()

            self._initialized = True
        
        except Exception:
            exc_logger()
        
    def update_df_movements(self, df_movements):
        """
        Updates the DataFrame containing movements.
        """
        self.DF_MOVEMENTS = df_movements.copy()
        log_status(message=f"Movements DataFrame updated with {len(df_movements)} records.")

    def update_df_movements_excluded(self, df_movements):
        """
        Updates the DataFrame containing movements.
        """
        self.DF_MOVEMENTS_EXCLUDED_FROM_OPT = df_movements.copy()
        log_status(message=f"Movements DataFrame updated with {len(df_movements)} records.")

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

        self.DELTA_GLOBAL_ERROR = f"{self.DELTA_GLOBAL_ERROR}. {message}" if self.DELTA_GLOBAL_ERROR else message

        self.log_info(message=msg2log)

    def log_warnning(self, message='', **kwargs):
        """
        Logs a warrning message to the log file.
        """
        if 'remarks' in kwargs:
            message = f"{message}. {kwargs['remarks']} " if message else kwargs['remarks']

        timestamp = str(datetime.now())[:19]
        msg2log = f"\n{timestamp}|{message}"

        self.DELTA_GLOBAL_WARNING = f"{self.DELTA_GLOBAL_WARNING}. {message}" if self.DELTA_GLOBAL_WARNING else message

        self.log_info(message=msg2log)

    def log_statusbar(self, message):
        self.log_info(message = f"{message}")
        STATUS_CONTROLLER.PROGRESS_INFO = f"{message}"


    def log_message(self, message=''):
        self.log_info(message=message)

    def log_info(self, message=''):

        timestamp = str(datetime.now())[:19]
        msg2log = f"\n{timestamp}: {message}"

        logging.info(msg2log)

        log_status(message=msg2log)


DELTA_LOGGER = DeltaLogFile.get_instance()