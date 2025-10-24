import logging
from os import getenv
import struct
from sqlalchemy import create_engine, text
from lion.logger.exception_logger import log_exception
from urllib.parse import quote_plus
import msal
import pyodbc
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine


TENANT_ID = getenv("AZURE_LION_APP_TENANT_ID")
CLIENT_ID = getenv("AZURE_LION_APP_CLIENT_ID")
CLIENT_SECRET = getenv("AZURE_LION_APP_CLIENT_SECRET")
AZURE_SQL_SERVER = getenv("AZURE_SQL_SERVER", "lion-server.database.windows.net")
AZURE_SQL_DB = getenv("AZURE_SQL_DB", "lion-sql-db")
AZURE_SQL_USER = getenv("AZURE_SQL_USER")
AZURE_SQL_PASS = getenv("AZURE_SQL_PASS")

"""
# Grant your app permission to query the database
**NOTE:** The following SQL commands should be run in the Azure SQL Database to create the user for the application and assign roles.
    CREATE USER [lion-app] FROM EXTERNAL PROVIDER;
    ALTER ROLE db_datareader ADD MEMBER [lion-app]; // read-only access
    ALTER ROLE db_datawriter ADD MEMBER [lion-app]; // read and write access
"""

def build_azure_ad_engine()-> str:
    """
    Build an Azure AD SQLAlchemy engine using the MSAL library for authentication.
    Currently not used due to connection issues; kept for reference.
    """
    try:
        app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENT_SECRET,
        )

        if not hasattr(pyodbc, "SQL_COPT_SS_ACCESS_TOKEN"):
            pyodbc.SQL_COPT_SS_ACCESS_TOKEN = 1256

        # Scope should have one slash
        result = app.acquire_token_for_client(scopes=["https://database.windows.net/.default"])
        if "access_token" not in result:
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")

        # Correct encoding (UTF-8)
        token_bytes = result["access_token"].encode("utf-8")

        # Pack properly for pyodbc
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)

        # ODBC connection string
        odbc_str = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={quote_plus(AZURE_SQL_SERVER)};"
            f"Database={quote_plus(AZURE_SQL_DB)};"
            f"Encrypt=yes;TrustServerCertificate=yes;"
            f"Connection Timeout=30;"
        )

        conn_str = f"mssql+pyodbc:///?odbc_connect={odbc_str}"

        # Correct usage for SQLAlchemy 2.x
        engine = create_engine(
            conn_str,
            connect_args={"attrs_before": {pyodbc.SQL_COPT_SS_ACCESS_TOKEN: token_struct}},
        )

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logging.info("Azure AD connection succeeded.")

        return conn_str

    except Exception as e:
        log_exception(f"build_azure_ad_engine: Failed to create Azure AD SQL engine: {e}")

    finally:
        try:
            engine.dispose()
        except:
            pass

    return ""

async def azure_connection():
    try:

        con_str_pid_pwd = (
            f"mssql+pyodbc://{quote_plus(AZURE_SQL_USER)}:{quote_plus(AZURE_SQL_PASS)}@{quote_plus(AZURE_SQL_SERVER)}/{quote_plus(AZURE_SQL_DB)}"
            "?driver=ODBC+Driver+18+for+SQL+Server"
            "&Encrypt=yes&TrustServerCertificate=no&Connection Timeout=30"
        )
    
        # Convert to async connection string
        async_con_str = con_str_pid_pwd.replace("mssql+pyodbc://", "mssql+aioodbc://")
        
        # Test async connection
        async_engine = create_async_engine(async_con_str)
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logging.info("="*20)
            logging.info("SQL authentication through uid/pwd async connection succeeded.")
            logging.info("="*20)
        await async_engine.dispose()
        return async_con_str

    except pyodbc.Error:
        logging.info("azure_connection: pyodbc Error occurred while connecting to Azure SQL DB with uid/pwd.") 

    except Exception:
        logging.info("azure_connection: General error occurred while connecting to Azure SQL DB with uid/pwd.")
    
    return ""

async def azure_connection_with_retry(max_retries=5, delay=5):
    for attempt in range(1, max_retries + 1):
        try:
            conn_str = await azure_connection()
            if conn_str:
                logging.info(f"Azure connection established on attempt {attempt}")
                async_con_str = conn_str.replace("mssql+aioodbc://", "mssql+pyodbc://")
                return async_con_str
            else:
                logging.warning(f"Attempt {attempt}: Connection not yet available.")
        except Exception as e:
            logging.error(f"Attempt {attempt} failed: {e}")

        if attempt < max_retries:
            logging.info(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)

    logging.error("All retry attempts failed to connect to Azure SQL.")
    return ""
