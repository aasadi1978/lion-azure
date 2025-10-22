from shutil import copyfile
from time import sleep
import lion.config.paths as paths
from lion.bootstrap.constants import LION_SCHEDULE_DATABASE_NAME

from lion.logger.status_logger import log_message
import lion.logger.exception_logger as LOGGER

def backup():

    try:
        copyfile(paths.LION_SQLDB_PATH / LION_SCHEDULE_DATABASE_NAME, paths.LION_SHARED_ASSETS_PATH / 'sqldb' / LION_SCHEDULE_DATABASE_NAME)
        sleep(0.1)

        if (paths.LION_SHARED_ASSETS_PATH / 'sqldb' / LION_SCHEDULE_DATABASE_NAME).exists():
            log_message(f"The database {LION_SCHEDULE_DATABASE_NAME} has been successfully backed up!")
        else:
            raise Exception(
                f"The database {LION_SCHEDULE_DATABASE_NAME} WAS NOT copied successully!")

    except Exception:
        dbs_exported = f"{LOGGER.log_exception(
            popup=False, remarks=f"Exporting {LION_SCHEDULE_DATABASE_NAME} failed!")}"

    return dbs_exported
