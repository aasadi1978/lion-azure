
import logging
from lion.bootstrap.constants import LION_MASTER_DATABASE_NAME
from shutil import copyfile
from time import sleep

from lion.config.paths import LION_SHARED_ASSETS_PATH, LION_SQLDB_PATH
from lion.maintenance.vacuum_db import compress_db_storage
from lion.utils.is_file_updated import is_file_updated

def export(if_updated_only: bool = False) -> str:

    err = ''
    try:

        if if_updated_only:

            if not is_file_updated(filename=LION_MASTER_DATABASE_NAME, Path=LION_SQLDB_PATH):
                logging.info(f'No changes detected in master data. Export skipped.')
                return 'skipped'

        compress_db_storage(db_paths=[LION_SQLDB_PATH / LION_MASTER_DATABASE_NAME])
        
        copyfile(
            LION_SQLDB_PATH / LION_MASTER_DATABASE_NAME, LION_SHARED_ASSETS_PATH / 'sqldb' / LION_MASTER_DATABASE_NAME)
        
        sleep(1)

        if not (LION_SHARED_ASSETS_PATH / 'sqldb' / LION_MASTER_DATABASE_NAME).exists():
            raise FileNotFoundError(f'{LION_MASTER_DATABASE_NAME} not found in shared assets.')

    except Exception as e:
        err = f'{err}Importing databases failed! {str(e)}'
        logging.error(err)

    if not err:
        logging.info(f'Exported {LION_MASTER_DATABASE_NAME} to {LION_SHARED_ASSETS_PATH / "sqldb" / LION_MASTER_DATABASE_NAME}.')
        if if_updated_only:
            return f'Changes detected in master data. Export completed.'

    return err
