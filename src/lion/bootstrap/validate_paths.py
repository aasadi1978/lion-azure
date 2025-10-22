import logging
from os import listdir, remove
from pathlib import Path
from inspect import getmembers
from shutil import copyfile
from lion.config import paths
from lion.bootstrap.constants import (LION_MASTER_DATABASE_NAME, LION_TEMP_SCENARIO_DATABASE_NAME, 
                                      LION_USER_DATABASE_NAME, LION_SCHEDULE_DATABASE_NAME)

def validate_all():

    for name, value in getmembers(paths):
        
        try:
            if isinstance(value, Path):
                path = Path(value).resolve()
                if not path.exists() and not str(path).lower().endswith('.db'):
                    path.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logging.error(f"Path validation failed for {name}: {path}")

    try:

        PR_LION_USER_DB = paths.LION_SQLDB_PATH / LION_USER_DATABASE_NAME
        PR_LION_LOCAL_SCHEDULE_DB = paths.LION_SQLDB_PATH / LION_SCHEDULE_DATABASE_NAME

        if not PR_LION_USER_DB.exists():
            copyfile(paths.LION_DEFAULT_SQLDB_PATH / LION_USER_DATABASE_NAME, PR_LION_USER_DB)

        if not paths.PR_LION_LOCAL_SCHEDULE_DB.exists():
            copyfile(paths.LION_DEFAULT_SQLDB_PATH / LION_SCHEDULE_DATABASE_NAME, paths.PR_LION_LOCAL_SCHEDULE_DB)

        if not listdir(paths.LION_SHARED_SCHEDULE_PATH):
            copyfile(paths.PR_LION_LOCAL_SCHEDULE_DB, paths.LION_SHARED_SCHEDULE_PATH / 'lion_default_schedule v.1.db')

        if not paths.PR_LION_MASTER_DATA_DB.exists():
            copyfile(paths.LION_DEFAULT_SQLDB_PATH / LION_MASTER_DATABASE_NAME, paths.PR_LION_MASTER_DATA_DB)

        status = paths.LION_SQLDB_PATH.exists()
        status = status and PR_LION_USER_DB.exists()
        status = status and PR_LION_LOCAL_SCHEDULE_DB.exists()

        if not status:
            raise FileExistsError(f"One or more sqldb databases not found in {paths.LION_SQLDB_PATH}")

    except Exception as e:
        logging.error(f"Error validating SQL database paths: {e}\n")
    
    logging.debug("Path validation completed successfully.")
