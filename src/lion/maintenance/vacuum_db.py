import logging
from os.path import basename
import sqlite3
from lion.config.paths import LION_SQLDB_PATH, PR_LION_USER_DB_PATH, PR_LION_LOCAL_SCHEDULE_DB
from lion.logger.exception_logger import log_exception

sqldb_path = LION_SQLDB_PATH

dct_config = {
    'lion_db': PR_LION_USER_DB_PATH,
    'local_schedule_db': PR_LION_LOCAL_SCHEDULE_DB
}

def compress_db_storage(db_paths=[]):
    """
    Compresses SQLite database files by running the VACUUM command on each specified database path.
    Args:
        db_paths (list, optional): List of file paths to SQLite database files. If not provided or empty,
            the function uses all database paths from the global `dct_config` dictionary.
    Returns:
        dict: A dictionary containing:
            - "code" (int): 200 if all VACUUM operations succeeded, 400 if any errors occurred.
            - "message" (str): A summary message indicating success or detailing encountered errors.
    Notes:
        - Logs exceptions using the `log_exception` function.
        - If any database fails to vacuum, the error messages are concatenated and returned.
    """

    if not db_paths:
        db_paths = list(dct_config.values())

    error_occurred = ''
    for dbpath in db_paths:

        try:
            conn = sqlite3.connect(dbpath)
            cursor = conn.cursor()
            cursor.execute("VACUUM;")
            conn.commit()
            conn.close()

        except sqlite3.Error as e:
            error_occurred = error_occurred + log_exception(
                popup=False, remarks=f"VACUUM failed for {basename(dbpath)} due to SQLite error {str(e)}!") + '; '

        except Exception as e:
            error_occurred = error_occurred + log_exception(
                popup=False, remarks=f"VACUUM failed for {basename(dbpath)}: {str(e)}!") + '; '

        finally:
            try:
                conn.close()
            except Exception:
                pass

            if error_occurred:
                logging.error(f"VACUUM failed for {basename(dbpath)}: {error_occurred}")
            else:
                logging.info(f"VACUUM completed for {basename(dbpath)} successfully.")

    return {"code": 400 if error_occurred else 200, 
            "message": error_occurred[: min(200, len(error_occurred))] if error_occurred else "VACUUM completed successfully!"}
