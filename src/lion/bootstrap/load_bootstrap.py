from os import environ, getenv
from pathlib import Path
import sys
from dotenv import load_dotenv

from lion.logger.exception_logger import log_exception
from lion.logger.status_logger import log_message


# Current directory of the project decided by the user. Note that this is not necessarily where the python package sits.
LION_PROJECT_HOME = Path(getenv('LION_PROJECT_HOME', str(Path().resolve()))).resolve()
LION_ENV_FILE_PATH = LION_PROJECT_HOME / '.env'
LION_BING_API_KEY = getenv('LION_BING_API_KEY', 'GET_MAP_KEY') # Allows to use user's Bing API key if set on device level
# load_dotenv override will not override this variable if set on device level instead of .env

# Directory where the lion package modules sit, e.g., lion\static, lion\templates, lion\sqldb etc.
LION_PKG_MODULES_PATH = Path(getenv('LION_PKG_MODULES_PATH', Path(__file__).resolve().parent.parent))
LION_LOG_FILE_PATH = Path(getenv('LION_LOG_FILE_PATH', LION_PROJECT_HOME / 'status.log'))
AZURE_STORAGE_CONNECTION_STRING = getenv("AZURE_STORAGE_CONNECTION_STRING")

try:

    if LION_ENV_FILE_PATH.exists():
        load_dotenv(dotenv_path=LION_ENV_FILE_PATH, override=True)

    # Read environment variables
    AZURE_SQL_SERVER = getenv("AZURE_SQL_SERVER", "azur-2285js-v10.database.windows.net")
    AZURE_SQL_DB = getenv("AZURE_SQL_DB", "lion-azure-sql-db")
    AZURE_SQL_USER = getenv("AZURE_SQL_USER")  # Optional for fallback
    AZURE_SQL_PASS = getenv("AZURE_SQL_PASS")  # Optional for fallback

    environ['AZURE_SQL_SERVER'] = AZURE_SQL_SERVER
    environ['AZURE_SQL_DB'] = AZURE_SQL_DB
    if AZURE_SQL_USER:
        environ['AZURE_SQL_USER'] = AZURE_SQL_USER
    if AZURE_SQL_PASS:
        environ['AZURE_SQL_PASS'] = AZURE_SQL_PASS

    # Ensure that the shared directory exists. If a local version exists, which can be used for testing, then use that one.
    # Otherwise, use the one set in the environment variable or else create a new one in the application root directory.
    # To avoid using the local version in production, remove the LION_TEMP_SHARED_DIR environment variable from the .env file.
    LION_SHARED_DIR_NAME = getenv('LION_TEMP_SHARED_DIR', 'LION-Shared')
    LION_TEMP_SHARED_DIR = LION_PROJECT_HOME / LION_SHARED_DIR_NAME
    LION_SHARED_DIR = LION_TEMP_SHARED_DIR if Path(LION_TEMP_SHARED_DIR).exists() else Path(getenv('LION_SHARED_DIR', str(
        LION_PROJECT_HOME / LION_SHARED_DIR_NAME))).resolve()
    LION_SHARED_DIR.mkdir(parents=True, exist_ok=True)

    # Making the following paths available for their consumer paths.py module
    environ['LION_PROJECT_HOME'] = str(LION_PROJECT_HOME)
    environ['LION_LOG_FILE_PATH'] = str(LION_LOG_FILE_PATH)
    environ['LION_STATIC_PATH'] = str(LION_PKG_MODULES_PATH / "static")
    environ['LION_TEMPLATES_PATH'] = str(LION_PKG_MODULES_PATH / "templates")
    environ['LION_DEFAULT_SQLDB_PATH'] = str(LION_PKG_MODULES_PATH / "sqldb")

    environ['LION_DEBUG_MODE'] = 'TRUE' if (LION_PROJECT_HOME / '.debug_mode_on').exists() else 'FALSE'
    environ['LION_BING_API_KEY'] = '' if not LION_BING_API_KEY else LION_BING_API_KEY
    
    # Potentially coming from .env file or else set to default values
    environ['LION_ENV'] = getenv('LION_ENV', 'local')  # 'local' or 'cloud'
    environ['LION_SHARED_DIR'] = str(LION_SHARED_DIR)


except Exception:
   log_exception(remarks="Failed to initialize env variables. Exiting with code 1.", level='critical')
   sys.exit(1)

LION_ENVIRONMENT_VARIABLES: dict = {name: value for name, value in environ.items() if name.startswith('LION_')}
log_message(f"Bootstrap environment variables loaded successfully.")

