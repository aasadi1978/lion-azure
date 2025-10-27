from os import getenv
from pathlib import Path

# The following paths are calculated and assigned to environment variables in lion\__init__.py when the lion package is loaded.
# We need them to be available as early as possible, i.e., when the app and db are created in create_flask_app/create_app.py
LION_PROJECT_HOME = Path(getenv('LION_PROJECT_HOME')).resolve()
LION_STATIC_PATH = Path(getenv('LION_STATIC_PATH')).resolve()
LION_TEMPLATES_PATH = Path(getenv('LION_TEMPLATES_PATH')).resolve()
LION_DEFAULT_SQLDB_PATH = Path(getenv('LION_DEFAULT_SQLDB_PATH')).resolve()
LION_LOG_FILE_PATH = Path(getenv('LION_LOG_FILE_PATH')).resolve()
LION_SHARED_DIR = Path(getenv('LION_SHARED_DIR')).resolve()
LION_DRIVER_REPORT_DIST_PATH = LION_PROJECT_HOME / "DriverReportDist"
LION_ARCGIS_PATH = LION_PROJECT_HOME / "ArcGIS"
LION_CONSOLIDATED_REPORT_PATH = LION_PROJECT_HOME / "ConsolidatedReports"

LION_OPTIMIZATION_PATH = LION_PROJECT_HOME / "optimisation"
DELTA_DATA_PATH = LION_PROJECT_HOME / "DeltaData"
DELTA_DATA_LOG_PATH = DELTA_DATA_PATH / "logs"

LION_LOCAL_DRIVER_REPORT_PATH = LION_PROJECT_HOME / "DriverReport"
LION_LOGS_PATH = LION_PROJECT_HOME / "logs"
LION_DIAGNOSTICS_PATH = LION_LOGS_PATH / "diagnostics"

LION_JS_PATH = LION_STATIC_PATH / 'js'
LION_FILES_PATH = LION_STATIC_PATH / 'files'
LION_IMAGES_PATH = LION_STATIC_PATH / 'images'
LION_FONTS_PATH = LION_STATIC_PATH / 'fonts'

# Temporary paths for optimization data dumps
TEMP_APP_DATA_FOLDER = LION_PROJECT_HOME / 'tmp'
LION_TEMP_OPTIMIZATION_DATA_DUMP_PATH = TEMP_APP_DATA_FOLDER / 'TempOptimizationDataDump'
LION_TEMP_DELTA_DATA_DUMP_PATH = TEMP_APP_DATA_FOLDER / 'delta-tmp'
