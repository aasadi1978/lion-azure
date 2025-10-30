import logging
from os import getenv
from pathlib import Path
from inspect import getmembers


def validate_all():

    if getenv("AZURE_STORAGE_CONNECTION_STRING") is None:
        logging.warning("AZURE_STORAGE_CONNECTION_STRING environment variable is not set. Azure Blob Storage features will be disabled.")

    from lion.config import paths

    for name, value in getmembers(paths):
        try:
            if isinstance(value, Path):
                path = Path(value).resolve()
                if not path.exists() and not str(path).lower().endswith('.db'):
                    path.mkdir(parents=True, exist_ok=True)

                logging.info(f"Created directory: {path}: {path.exists()}")
                
        except Exception as e:
            logging.error(f"Path validation failed for {name}: {path} ({e})")

    logging.debug("Path validation completed successfully.")
