from os import getenv, remove
from pathlib import Path
from pandas import read_sql_table
from sqlalchemy import create_engine, text
import logging


def verifyDistanceTimeTablePresence():

    master_db_path = Path(getenv('LION_HOME_PATH')) / "sqldb" / "lion_master_data.db"
    if not master_db_path.exists():
        return False

    master_data_engine = create_engine(f'sqlite:///{master_db_path}')

    with master_data_engine.connect() as conn:

        try:
            verify_qry = text("""SELECT name FROM sqlite_master WHERE type='table' AND name='DistanceTime';""")
            if conn.execute(verify_qry).fetchone():
                return True

        except Exception as e:
            logging.error(f"An error occurred when ensuring DistanceTime table exists: {str(e)}")

        finally:
            master_data_engine.dispose()

    return False

def upgrade_master_data():

    lion_sqldb_path =  Path(getenv('LION_HOME_PATH')) / "sqldb"
    group_name_default = getenv('LION_USER_GROUP_NAME', 'fedex-lion-uk-users')

    master_db_path = lion_sqldb_path / "lion_master_data.db"

    if master_db_path.exists():

        try:
            master_data_engine = create_engine(f'sqlite:///{master_db_path}')

            if not verifyDistanceTimeTablePresence():

                runtime_db_path = lion_sqldb_path / "lion_runtimes_default.db"
                if runtime_db_path.exists():

                    runtime_source_engine = create_engine(f'sqlite:///{runtime_db_path}')
                    try:

                        df = read_sql_table('DistanceTime', con=runtime_source_engine)
                        if not df.empty:
                            df.to_sql('DistanceTime', con=master_data_engine, if_exists='replace', index=False)

                            if not verifyDistanceTimeTablePresence():
                                raise ValueError("DistanceTime table could not be migrated to lion_master_data.db")

                        runtime_source_engine.dispose()
                        remove(runtime_db_path)

                    except Exception as e:
                        logging.critical(f"An error occurred when migrating DistanceTime table: {str(e)}")

                else:
                    logging.critical("DistanceTime table is missing in lion_master_data.db and lion_runtimes_default.db could not be found.")


            # Ensure group_name column exists in DistanceTime and location tables
            for tbl in ['DistanceTime', 'location']:

                with master_data_engine.connect() as connection:

                    action = f'upgrade {tbl} table'
                    verify_qry = text(f"""SELECT distinct group_name FROM {tbl};""")

                    try:
                        connection.execute(verify_qry)
                    except Exception as e:
                        logging.warning(f"An error occurred when executing {action}: {str(e)}. Creating missing column group_name in {tbl} table.")
                        try:
                            connection.execute(text(f"ALTER TABLE {tbl} ADD COLUMN group_name TEXT;"))
                            logging.info(f"Column group_name has been successfully created in the {tbl} table.")
                        except Exception as e:
                            logging.error(f"An error occurred when executing {action}: {str(e)}")

                        try:
                            connection.execute(text(f"UPDATE {tbl} SET group_name='{group_name_default}';"))
                            connection.commit()
                            logging.info(f"Column group_name has been successfully updated in the {tbl} table.")
                        except Exception as e:
                            logging.error(f"An error occurred when executing {action}: {str(e)}")
                    
                    else:
                        logging.info(f"Column group_name already exists in the {tbl} table.")

        except Exception as e:
            logging.error(f"An error occurred when disposing master_data_engine: {str(e)}")
        
        finally:
            if master_data_engine:
                master_data_engine.dispose()

