from lion.delta_suite.delta_logger import DELTA_LOGGER
from pyodbc import connect as pyodbc_connect

def table_exists(cursor, tblname=''):
    return any(
                row.table_name.lower() == tblname.lower()
                for row in cursor.tables(tableType='TABLE')
            )

def verify_db_tables(accdb_path, 
                      tblnames=['G302_Hubs', 'G301_Depots', 'G300_Locations', 'G410_DistanceTime']) -> str:
    
    """
    Validates the structure of a Microsoft Access database by checking for the existence of required tables.
    Args:
        accdb_path (str): The file path to the Access database (.accdb or .mdb).
    Returns:
        pyodbc.Connection or None or bool:
            - Returns the database connection object if all required tables exist.
            - Returns None if any required table is missing.
            - Returns False if an exception occurs during validation.
    Raises:
        None. All exceptions are caught and handled internally.
    Side Effects:
        Logs exceptions and updates status using internal methods if validation fails.
    """
    try:

        access_conn_str = (r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            rf"DBQ={accdb_path};"
        )

        access_conn = pyodbc_connect(access_conn_str)
        cursor = access_conn.cursor()

        if not all(table_exists(cursor, tblname) for tblname in tblnames):
            access_conn_str = ''

    except Exception as e:
        DELTA_LOGGER.log_exception(f"Error validating the database: {str(e)}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'access_conn' in locals():
            access_conn.close()

    return access_conn_str