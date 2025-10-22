import logging
from os import getenv
from sqlalchemy import create_engine, text
from lion.logger.exception_logger import log_exception
from urllib.parse import quote_plus
from sqlalchemy.exc import SQLAlchemyError

def encode_odbc_string(odbc_str):
    return quote_plus(odbc_str)

def test_connection_string(sql_connection_string: str) -> bool:
    try:

        engine = create_engine(sql_connection_string, echo=False, future=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM TestEmployees;"))
            logging.info("Connection test succeeded.")
            return True
    except SQLAlchemyError as e:
        logging.error(f"Connection test failed: {e}")
        return False

    
def azure_connection():
    try:

        AZURE_SQL_SERVER = getenv("AZURE_SQL_SERVER", "lion-server.database.windows.net")
        AZURE_SQL_DB = getenv("AZURE_SQL_DB", "lion-sql-db")
        AZURE_SQL_USER = getenv("AZURE_SQL_USER")
        AZURE_SQL_PASS = getenv("AZURE_SQL_PASS")

        sql_authentication = (f"mssql+pyodbc://{quote_plus(AZURE_SQL_USER)}:{quote_plus(AZURE_SQL_PASS)}@{quote_plus(AZURE_SQL_SERVER)}/{quote_plus(AZURE_SQL_DB)}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&Encrypt=yes&TrustServerCertificate=no&Connection Timeout=30")

        if test_connection_string(f"{sql_authentication}"):
            return sql_authentication

        logging.error("All Azure SQL DB connection string attempts failed.")
        return ""
        
    except Exception:
        log_exception("configure_lion_app: Failed to create Azure SQL DB connection string")
        return ""

