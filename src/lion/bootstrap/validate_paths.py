import logging
from os import getenv
from pathlib import Path
from inspect import getmembers
from lion.config import paths
from lion.bootstrap.constants import (LION_SQLITE_LOCAL_DATABASE)

def validate_all():

    if getenv("AZURE_STORAGE_CONNECTION_STRING") is None:
        logging.warning("AZURE_STORAGE_CONNECTION_STRING environment variable is not set. Azure Blob Storage features will be disabled.")

        for name, value in getmembers(paths):
            
            try:
                if isinstance(value, Path):
                    path = Path(value).resolve()
                    if not path.exists() and not str(path).lower().endswith('.db'):
                        path.mkdir(parents=True, exist_ok=True)

            except Exception as e:
                logging.error(f"Path validation failed for {name}: {path}")

    try:
        PR_LION_USER_DB = paths.LION_DEFAULT_SQLDB_PATH / LION_SQLITE_LOCAL_DATABASE
        status = PR_LION_USER_DB.exists()

        if not status:
            raise FileExistsError(f"One or more sqldb databases not found in {paths.LION_SQLDB_PATH}")

    except Exception as e:
        logging.error(f"Error validating SQL database paths: {e}\n")
    
    logging.debug("Path validation completed successfully.")
