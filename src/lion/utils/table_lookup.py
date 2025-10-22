from pathlib import Path
from sqlalchemy import create_engine, text

def table_exists_in_db(sqldb_path: Path = None, tablename: str = 'DistanceTime') -> bool:
    """
    Checks if a specified table exists in a SQLite database.
    Args:
        sqldb_path (Path, optional): The path to the SQLite database file. Defaults to None.
        tablename (str, optional): The name of the table to check for existence. Defaults to 'DistanceTime'.
    Returns:
        bool: True if the table exists in the database, False otherwise.
    """

    tbl_exist = False

    if sqldb_path.exists():
        db_engine = create_engine(f'sqlite:///{sqldb_path}')

        with db_engine.connect() as connection:

            if connection.execute(
                text(f"""SELECT name FROM sqlite_master WHERE type='table' AND name='{tablename}';""")).fetchone():

                tbl_exist = True
            
            db_engine.dispose()

        return tbl_exist