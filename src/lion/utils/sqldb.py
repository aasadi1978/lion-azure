from lion.logger.status_logger import log_message
from sqlalchemy import Table, func, select, delete
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from sqlite3 import OperationalError
from pandas import DataFrame, read_sql as pd_read_sql
from lion.logger.exception_logger import log_exception


class SqlDb():

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls):
        return cls()

    def sqlalchemy_select(self, tablename='', bind=None):

        # Use Flask-SQLAlchemy's Metadata instance
        _meta_data = LION_SQLALCHEMY_DB.metadata

        try:

            if bind:
                engine = LION_SQLALCHEMY_DB.get_engine(bind=bind)
            else:
                engine = LION_SQLALCHEMY_DB.get_engine()

            sql_table = Table(tablename, _meta_data, autoload_with=engine)

            tbl_columns = [str(x).replace(tablename + '.', '')
                           for x in sql_table.columns]

            stmt = select(sql_table)
            with engine.begin() as connection:
                results = connection.execute(stmt).fetchall()

        except Exception:
            print(log_exception(
                popup=False, remarks=f"select query failed for {tablename}."))

            return DataFrame()

        return DataFrame(results, columns=tbl_columns)

    def to_sql(self, dataFrame, destTableName, ifExists='append', dct_toColumn={}, bind=None):

        # Get the engine for the specified bind, if provided
        if bind:
            engine = LION_SQLALCHEMY_DB.get_engine(bind=bind)
        else:
            engine = LION_SQLALCHEMY_DB.get_engine()

        _meta_data = LION_SQLALCHEMY_DB.metadata

        try:
            if dct_toColumn:
                dataFrame.rename(columns=dct_toColumn, inplace=True)

            try:
                existing_table = Table(
                    destTableName, _meta_data, autoload_with=engine)

                # Get the column names of the existing table
                existing_columns = [column.name for column in existing_table.columns]

                # Drop columns from the DataFrame that are not in the existing table
                dataFrame = dataFrame[[col for col in dataFrame.columns 
                                       if col in existing_columns]].copy()

                if ifExists == 'replace':
                    delete_statement = delete(existing_table)
                    with engine.begin() as connection:
                        connection.execute(delete_statement)
                    ifExists = 'append'

            except Exception:
                log_exception(popup=False)
                # Table doesn't exist. This is okay since we might be creating it.
                pass

            with engine.begin() as connection:
                dataFrame.to_sql(destTableName, con=connection,
                                 if_exists=ifExists, index=False)

        except Exception:
            # The context manager will handle the transaction rollback
            log_exception(popup=False)
            return 0

        log_message(f"Data has been written to {destTableName} successfully.")
        return 1

    def read_sql(self, sqlstr='', bind=None):
        try:
            if bind:
                engine = LION_SQLALCHEMY_DB.get_engine(bind=bind)
            else:
                engine = LION_SQLALCHEMY_DB.get_engine()

            return pd_read_sql(sqlstr, engine)

        except OperationalError:
            log_exception(popup=False, remarks=f"SQL error occurred while reading SQL: {sqlstr}. An empty DataFrame will be returned.")
            return DataFrame()


    def empty_table(self, tablename='', bind=None):
        try:
            engine = LION_SQLALCHEMY_DB.get_engine(bind=bind) if bind else LION_SQLALCHEMY_DB.get_engine()

            # Reflect the table from the database
            sql_table = Table(tablename, LION_SQLALCHEMY_DB.metadata, autoload_with=engine)

            with engine.begin() as connection:
                # Delete all rows
                connection.execute(delete(sql_table))

                # Check if the table is empty
                count_stmt = select(func.count()).select_from(sql_table)
                result = connection.execute(count_stmt).scalar()

                if result != 0:
                    log_exception(popup=False, remarks=f"Table {tablename} not empty after delete!")
                    return 0

        except Exception as e:
            log_exception(popup=False, remarks=f"Emptying table {tablename} failed! Exception: {e}")
            return 0

        return 1

SQLDB = SqlDb.get_instance()