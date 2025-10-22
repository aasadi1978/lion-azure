from datetime import datetime
import logging
from os import remove
from pathlib import Path
from time import sleep
import zipfile
from lion.bootstrap.constants import TAG_NAME
from lion.config.paths import LION_ONBOARDING_PATH
from lion.logger.exception_logger import log_exception
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER
import threading


class RetrieveLionWheelVersion:

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        pass

    def initialize(self):

        if not self._initialized:

            self.__lion_current_version: str = str(TAG_NAME).replace("lion-", "").strip()
            self.__new_lion_whl_version: str = str(TAG_NAME).replace("lion-", "").strip()
            self.__continue_checking: bool = True

            self._initialized = True
            self._start_time = datetime.now()

            if Path("lion_update.trigger").exists():
                remove("lion_update.trigger")
                
            self.__start_monitoring_new_version()
            
    
    @classmethod
    def get_instance(cls):
        return cls()

    def __start_monitoring_new_version(self) -> bool:

        def monitor():
            while self.__continue_checking:
                try:
                    if self.retrieve_lion_wheel_version():
                        if self.__lion_current_version != self.__new_lion_whl_version:
                            self.__continue_checking = False

                            with open("lion_update.trigger", "w") as f:
                                f.write(f"LION {self.__new_lion_whl_version} is available.")

                            STATUS_CONTROLLER.POPUP_MESSAGE = (
                                f"LION {self.__new_lion_whl_version} is available! Up/downgrade will start soon automatically."
                            )
                            logging.info(
                                f"New LION version {self.__new_lion_whl_version} is available. Current version is {self.__lion_current_version}."
                            )
                            return True
                    sleep(300)  # Check every 5 minutes
                except Exception:
                    log_exception(remarks="Error when initializing version monitoring...")
            return False

        # Run monitoring in a background thread to avoid blocking
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        return True

    def _get_time_elapsed(self) -> float:
        try:
            return (datetime.now() - self._start_time).total_seconds() / 60
        except Exception:
            log_exception(remarks="Error calculating time elapsed")
            return 5
    
    def retrieve_lion_wheel_version(self) -> bool:

        try:
            whl_files = sorted(
                LION_ONBOARDING_PATH.glob("lion-*.whl"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )

            if not whl_files:
                logging.warning(f"No wheel files found in {LION_ONBOARDING_PATH}")
            else:
                with zipfile.ZipFile(whl_files[0], "r") as zf:
                    for name in zf.namelist():
                        if name.endswith("METADATA"):
                            with zf.open(name) as f:
                                for line in f:
                                    line = line.decode("utf-8").strip()
                                    if line.startswith("Version:"):
                                        logging.info(f"Found version line for LION whl file: {line}/{self.__lion_current_version}")
                                        self.__new_lion_whl_version = str(line).replace("Version:", "").strip()
                                        return True
        
        except Exception:
            log_exception(remarks="Error retrieving LION wheel version.")

        finally:
            # Reset the timer for the next check
            self._start_time = datetime.now()
        
        return False


RETTRIEVELIONVERSION = RetrieveLionWheelVersion.get_instance()