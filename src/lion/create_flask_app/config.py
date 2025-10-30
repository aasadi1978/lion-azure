from datetime import timedelta
import logging
from os import getenv
from pathlib import Path
from lion.create_flask_app.azure_sql_manager import SQLALCHEMY_DATABASE_URI

def configure_lion_app() -> dict:
    """
    Setup the application configuration.
    """

    try:

        db_path = Path(getenv('LION_PKG_MODULES_PATH')) / 'sqldb'/ 'data.db'
        LION_DEFAULT_SQLDB_PATH_BIND = f"sqlite:///{db_path}"

        lion_config = {}
        lion_config['SQLALCHEMY_BINDS'] = {'local_data_bind':  LION_DEFAULT_SQLDB_PATH_BIND}

        lion_config.update({
            'SQLALCHEMY_DATABASE_URI': SQLALCHEMY_DATABASE_URI,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'LION_USER_ID': lion_config.get('LION_USER_ID', 'Guest')
            })

        lion_config["SESSION_PERMANENT"] = True
        lion_config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

    except Exception as e:
        logging.error(f"[FATAL] Failed to load or parse flask config: {e}")
        return {}
    
    return lion_config

LION_CONFIG = configure_lion_app()
