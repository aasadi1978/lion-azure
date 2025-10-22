import logging
from os import getenv
from sqlalchemy import create_engine, text
from lion.logger.exception_logger import log_exception
from urllib.parse import quote_plus
from sqlalchemy.exc import SQLAlchemyError
import msal

TENANT_ID = getenv("AZURE_LION_APP_TENANT_ID")
CLIENT_ID = getenv("AZURE_LION_APP_CLIENT_ID")
CLIENT_SECRET = getenv("AZURE_LION_APP_CLIENT_SECRET")
AZURE_SQL_SERVER = getenv("AZURE_SQL_SERVER", "lion-server.database.windows.net")
AZURE_SQL_DB = getenv("AZURE_SQL_DB", "lion-sql-db")
AZURE_SQL_USER = getenv("AZURE_SQL_USER")
AZURE_SQL_PASS = getenv("AZURE_SQL_PASS")

def azure_ad_sql_connection():
    
    try:
        # Create an MSAL confidential client
        app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENT_SECRET
        )

        # Request a token for Azure SQL
        scope = ["https://database.windows.net//.default"]
        result = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in result:
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")

        access_token = result["access_token"]

        # Build SQLAlchemy connection string using access token
        connection_string = (
            f"mssql+pyodbc://@{quote_plus(AZURE_SQL_SERVER)}/{quote_plus(AZURE_SQL_DB)}"
            "?driver=ODBC+Driver+18+for+SQL+Server"
            "&Encrypt=yes&TrustServerCertificate=no"
        )

        # Pass token to SQLAlchemy engine
        from sqlalchemy import create_engine
        engine = create_engine(connection_string, connect_args={"attrs_before": {1256: access_token}})
        return engine
    
    except Exception:
        log_exception("azure_ad_sql_connection: Failed to create Azure AD SQL connection")
        return None

def test_azure_ad_connection() -> bool:
    try:
        engine = azure_ad_sql_connection()
        if engine is None:
            return False

        with engine.connect() as conn:
            result = conn.execute("SELECT TOP 1 * FROM TestEmployees;")
            print(result.fetchall())
            return True
    except SQLAlchemyError:
        log_exception(f"test_azure_ad_connection: Connection test failed")
        return False
    
    except Exception:
        log_exception(f"test_azure_ad_connection: Unexpected error during connection test")
        return False

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
        if test_azure_ad_connection():
            logging.info("Using Azure AD authentication for Azure SQL DB connection.")
            return azure_ad_sql_connection().url.__to_string__()
        
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

