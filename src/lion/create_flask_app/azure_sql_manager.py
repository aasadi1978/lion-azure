import logging
from os import getenv
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from urllib.parse import quote_plus
import pyodbc
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv()
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

SQLALCHEMY_DATABASE_URI = (
    f"mssql+pyodbc://{quote_plus(AZURE_SQL_USER)}:{quote_plus(AZURE_SQL_PASS)}@{quote_plus(AZURE_SQL_SERVER)}/{quote_plus(AZURE_SQL_DB)}"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Encrypt=yes&TrustServerCertificate=no&Connection Timeout=30"
)


def validate_db_connection(app: Flask):
    try:
        from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
        LION_SQLALCHEMY_DB.session.execute(text("SELECT 1"))
        return
    except SQLAlchemyError as e:
        logging.error(f"Database connection is not live!")

    try:
        if not asyncio.run(azure_connection_with_retry(app)):
            raise Exception('asyncio run azure_connection_with_retry failed!')
    except Exception:
        logging.error("Failed to establish sql database connection.")

async def is_azure_db_connection_ok(app: Flask):
    try:
        # Convert to async connection string
        sqlalchemy_db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        sqlalchemy_db_uri_async = sqlalchemy_db_uri.replace("mssql+pyodbc://", "mssql+aioodbc://")
        
        # Test async connection
        async_engine = create_async_engine(sqlalchemy_db_uri_async)
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logging.info("="*20)
            logging.info("SQL authentication through uid/pwd async connection succeeded.")
            logging.info("="*20)
        await async_engine.dispose()
        return True

    except pyodbc.Error:
        logging.info("azure_connection: pyodbc Error occurred while connecting to Azure SQL DB with uid/pwd.") 

    except Exception:
        logging.info("azure_connection: General error occurred while connecting to Azure SQL DB with uid/pwd.")
    
    return False

async def azure_connection_with_retry(max_retries=10, delay=5) -> bool:
    for attempt in range(1, max_retries + 1):
        try:
            connection_status = await is_azure_db_connection_ok()
            if connection_status:
                logging.info(f"Azure connection established on attempt {attempt}")
                return connection_status
            else:
                logging.warning(f"Attempt {attempt}: Connection not yet available.")

        except Exception as e:
            logging.error(f"Attempt {attempt} failed: {e}")

        if attempt < max_retries:
            logging.info(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)

    logging.error("All retry attempts failed to connect to Azure SQL.")
    return False
