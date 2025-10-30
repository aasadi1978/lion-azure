from os import getenv
from pathlib import Path
from lion.bootstrap.get_user import retrieve_current_user

# The following paths are calculated and assigned to environment variables in lion\__init__.py when the lion package is loaded.
# We need them to be available as early as possible, i.e., when the app and db are created in create_flask_app/create_app.py

user_id, user_name, group_name = retrieve_current_user()
user_id = str(user_id).replace(' ','')
user_name = str(user_name).replace(' ','')
group_name = str(group_name).replace(' ','')

PREFIX_MAP = {}

LION_PROJECT_HOME = Path(getenv('LION_PROJECT_HOME')).resolve()
LION_USER_HOME = Path(getenv('LION_PROJECT_HOME')).resolve() / user_name

LION_LOG_FILE_PATH = LION_USER_HOME / 'status.log'
LION_LOGS_PATH = LION_USER_HOME / 'logs'

LION_DRIVER_REPORT_DIST_PATH = LION_PROJECT_HOME / "DriverReportDist"
PREFIX_MAP[LION_DRIVER_REPORT_DIST_PATH] = f"{group_name}"

LION_ARCGIS_PATH = LION_PROJECT_HOME / "ArcGIS"
LION_CONSOLIDATED_REPORT_PATH = LION_PROJECT_HOME / "ConsolidatedReports"
PREFIX_MAP[LION_CONSOLIDATED_REPORT_PATH] = f"{group_name}"

LION_TEMPLATES_PATH=Path(getenv('LION_PKG_MODULES_PATH')).resolve() / 'templates'
LION_STATIC_PATH=Path(getenv('LION_PKG_MODULES_PATH')).resolve() / 'static'

LION_OPTIMIZATION_PATH = LION_USER_HOME / "optimisation"
PREFIX_MAP[LION_OPTIMIZATION_PATH] = f"{group_name}/{user_name}"

DELTA_DATA_PATH = LION_USER_HOME / "DeltaData"
DELTA_DATA_LOG_PATH = DELTA_DATA_PATH / "logs"

LION_LOCAL_DRIVER_REPORT_PATH = LION_LOGS_PATH / "DriverReport"
LION_DIAGNOSTICS_PATH = LION_LOGS_PATH / "diagnostics"

LION_JS_PATH = LION_STATIC_PATH / 'js'
LION_FILES_PATH = LION_STATIC_PATH / 'files'
LION_IMAGES_PATH = LION_STATIC_PATH / 'images'
LION_FONTS_PATH = LION_STATIC_PATH / 'fonts'

# Temporary paths for optimization data dumps
TEMP_APP_DATA_FOLDER = LION_USER_HOME / 'tmp-lion'
LION_TEMP_OPTIMIZATION_DATA_DUMP_PATH = TEMP_APP_DATA_FOLDER / 'TempOptimizationDataDump'
LION_TEMP_DELTA_DATA_DUMP_PATH = TEMP_APP_DATA_FOLDER / 'delta-tmp'

from lion.logger.logger_handler import initialize_logger
initialize_logger(log_file_path=LION_LOG_FILE_PATH, user_name=user_name)
import logging
logging.info("===================================================")
logging.info(f"Username: {user_name}")
logging.info(f"UserId: {user_id}")
logging.info("===================================================")
