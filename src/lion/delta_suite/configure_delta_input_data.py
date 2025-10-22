from os import listdir
from lion.config import paths
from lion.delta_suite.delta_logger import DELTA_LOGGER
from lion.delta_suite.verify_database_tables import verify_db_tables
from lion.delta_suite.verify_delta_output_xslx_file import validate_and_load_delta_excel
from pandas import DataFrame
from lion.utils.empty_dir import empty_dir

def check_and_set_delta_data_sources() -> bool:

    """
    Validates and assigns the delta database and movement Excel file from the specified data path.
    This function ensures that exactly one Access database file (.accdb or .accdb_) and one Excel file (.xlsx or .xlsm)
    are present in the given directory. It copies these files to a temporary directory, validates them, and updates
    the DELTA_LOGGER with their paths. If validation fails or multiple files of the same type are found, it logs an
    exception and resets the logger paths.

    Returns:
        bool: True if both the database and Excel file are found, validated, and assigned successfully; False otherwise.
    Assigns:
        DELTA_LOGGER.DBPATH = ''
    """

    try:

        empty_dir(paths.LION_TEMP_DELTA_DATA_DUMP_PATH)

        DELTA_LOGGER.DELTA_DB_CON_STR = ''
        
        list_of_accdb_names = [dbname for dbname in listdir(
            paths.DELTA_DATA_PATH) if dbname.lower().endswith('.accdb')]

        list_of_xlsx_names = [xl_file for xl_file in listdir(paths.DELTA_DATA_PATH)
                                if xl_file.lower().endswith('.xlsx') or xl_file.lower().endswith('.xlsm')]

        if len(list_of_xlsx_names) == 1 and len(list_of_accdb_names) == 1:

            dfiles = {
                'accdb': list_of_accdb_names.pop(),
                'xlsx': list_of_xlsx_names.pop()
            }

            accdb_filename = dfiles['accdb']
            access_conn_str = verify_db_tables(paths.DELTA_DATA_PATH / accdb_filename)

            if access_conn_str:
                DELTA_LOGGER.DELTA_DB_CON_STR = access_conn_str

            xlsx_filename = dfiles['xlsx']

            if not validate_and_load_delta_excel(xlFilePath=paths.DELTA_DATA_PATH / xlsx_filename):
                raise Exception(f"Excel file {xlsx_filename} is not valid or does not contain required data.")

            return not DELTA_LOGGER.DF_MOVEMENTS.empty and DELTA_LOGGER.DELTA_DB_CON_STR != ''

        else:
            raise Exception(
                f"Please check out the delta input directory " +
                f"and make sure there is only one version of each data type, i.e., movements and input database!")

    except Exception as e:
        DELTA_LOGGER.log_exception(message=f"Delta data could not be validated!. {str(e)}")

    DELTA_LOGGER.DELTA_DB_CON_STR = ''
    DELTA_LOGGER.update_df_movements(DataFrame())

    return False