from pathlib import Path
from os import environ, getenv
from lion.logger.logger_handler import initialize_logger
from dotenv import load_dotenv

initialize_logger()

environ['LION_PKG_MODULES_PATH'] = str(Path(__file__).resolve().parent)

# Current directory of the project decided by the user. Note that this is not necessarily where the python package sits.
LION_PROJECT_HOME = Path().resolve()
env_path = LION_PROJECT_HOME / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

environ['LION_BING_API_KEY'] = str(getenv('LION_BING_API_KEY', 'GET_MAP_KEY'))
environ['LION_DEBUG_MODE'] = 'TRUE' if (LION_PROJECT_HOME / '.debug_mode_on').exists() else 'FALSE'
environ['LION_ENV'] = getenv('LION_ENV', 'local')  # 'local' or 'cloud'
