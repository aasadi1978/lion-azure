import logging
from os import getenv
import jwt
import struct
from sqlalchemy import create_engine, text
from lion.logger.exception_logger import log_exception
from urllib.parse import quote_plus
from sqlalchemy.exc import SQLAlchemyError
import msal
import pyodbc


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



def azure_sql_connection_string_uid_pwd():
    try:
        return (
            f"mssql+pyodbc://{quote_plus(AZURE_SQL_USER)}:{quote_plus(AZURE_SQL_PASS)}@{quote_plus(AZURE_SQL_SERVER)}/{quote_plus(AZURE_SQL_DB)}"
            "?driver=ODBC+Driver+18+for+SQL+Server"
            "&Encrypt=yes&TrustServerCertificate=no&Connection Timeout=30"
        )

    except Exception:
        log_exception("azure_ad_token_credentials: Failed to acquire Azure AD token")
        return ""
    
def azure_ad_sql_connection_string():

    return (
        f"mssql+pyodbc://@{quote_plus(AZURE_SQL_SERVER)}/{quote_plus(AZURE_SQL_DB)}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&Encrypt=yes&TrustServerCertificate=no"
        "&Connection Timeout=30"
    )

def build_azure_ad_engine()-> str:

    # try:
    #     app = msal.ConfidentialClientApplication(
    #         CLIENT_ID,
    #         authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    #         client_credential=CLIENT_SECRET,
    #     )

    #     result = app.acquire_token_for_client(scopes=["https://database.windows.net//.default"])
    #     if "access_token" not in result:
    #         raise Exception(f"Failed to acquire token: {result.get('error_description')}")

    #     access_token = result["access_token"]
    #     token_bytes = result["access_token"].encode("utf-16-le")

    #     # claims = jwt.decode(result["access_token"], options={"verify_signature": False})
    #     # print("Tenant ID in token:", claims.get("tid"))
    #     # print("Audience:", claims.get("aud"))
    #     # print("App ID:", claims.get("appid"))

    #     # input("Press Enter to test ODBC connection...")
    #     # ✅ Raw ODBC connection string — no SQLAlchemy encoding here
    #     odbc_str = (
    #         "Driver={ODBC Driver 18 for SQL Server};"
    #         "Server=tcp:lion-server.database.windows.net,1433;"
    #         "Database=lion-sql-db;"
    #         "Encrypt=yes;"
    #         "TrustServerCertificate=no;"
    #         "Connection Timeout=30;"
    #     )

    #     # ✅ Pass token via attrs_before
    #     conn = pyodbc.connect(odbc_str, attrs_before={1256: token_bytes})
    #     input("Press Enter to execute test query...")
    #     cursor = conn.cursor()
    #     cursor.execute("SELECT TOP 1 name FROM sys.databases;")
    #     print(cursor.fetchall())

    # except pyodbc.Error as e:
    #     for arg in e.args:
    #         print("ODBC error:", arg)

    # except Exception:
    #     log_exception("build_azure_ad_engine: Failed to create Azure AD SQL engine")
    
    # input("Press Enter to continue...")
    # Acquire access token
    try:
        app = msal.ConfidentialClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            client_credential=CLIENT_SECRET,
        )

        if not hasattr(pyodbc, "SQL_COPT_SS_ACCESS_TOKEN"):
            pyodbc.SQL_COPT_SS_ACCESS_TOKEN = 1256

        # ✅ Scope should have one slash
        result = app.acquire_token_for_client(scopes=["https://database.windows.net/.default"])
        if "access_token" not in result:
            raise Exception(f"Failed to acquire token: {result.get('error_description')}")

        # ✅ Correct encoding (UTF-8)
        token_bytes = result["access_token"].encode("utf-8")

        # ✅ Pack properly for pyodbc
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)

        # ✅ ODBC connection string
        odbc_str = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server={quote_plus(AZURE_SQL_SERVER)};"
            f"Database={quote_plus(AZURE_SQL_DB)};"
            f"Encrypt=yes;TrustServerCertificate=yes;"
            f"Connection Timeout=30;"
        )

        conn_str = f"mssql+pyodbc:///?odbc_connect={odbc_str}"

        # ✅ Correct usage for SQLAlchemy 2.x
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

def test_connection_str_uid_pwd()-> str:
    try:
        sql_authentication_str = azure_sql_connection_string_uid_pwd()
        engine = create_engine(sql_authentication_str, echo=False, future=True)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logging.info("Connection test UID/PWD succeeded.")
            return sql_authentication_str
        
    except SQLAlchemyError as e:
        logging.error(f"Connection test UID/PWD failed: {e}")
    
    finally:
        engine.dispose()
    
    return ""

    
def azure_connection():
    try:
        # co_str_ad = build_azure_ad_engine()   
        # if co_str_ad:
        #     logging.info("Using Azure AD authentication for Azure SQL DB connection.")
        #     return co_str_ad
        
        if AZURE_SQL_USER is None or AZURE_SQL_PASS is None:
            logging.error("Azure SQL credentials are not set in environment variables.")
            return ""

        con_str = test_connection_str_uid_pwd()
        if con_str:
            logging.info("Using SQL authentication for Azure SQL DB connection.")
            return con_str

    except Exception:
        log_exception("configure_lion_app: Failed to create Azure SQL DB connection string")
    
    return ""
