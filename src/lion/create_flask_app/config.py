from datetime import timedelta
import logging
from os import getenv
from pathlib import Path

def enable_azure_env_config():
    """
    Enable Azure environment configuration if running in Azure.
    """

    db_path = Path(getenv('LION_PKG_MODULES_PATH')) / 'sqldb'/ 'data.db'
    LION_DEFAULT_SQLDB_PATH_BIND = f"sqlite:///{db_path}"
    return None, LION_DEFAULT_SQLDB_PATH_BIND

    from lion.create_flask_app.azure_sql_manager import SQLALCHEMY_DATABASE_URI
    return SQLALCHEMY_DATABASE_URI, LION_DEFAULT_SQLDB_PATH_BIND

def configure_lion_app() -> dict:
    """
    Setup the application configuration.
    """

    try:
        lion_config = {}

        SQLALCHEMY_DATABASE_URI, LION_DEFAULT_SQLDB_PATH_BIND = enable_azure_env_config()
        if SQLALCHEMY_DATABASE_URI is None and LION_DEFAULT_SQLDB_PATH_BIND is not None:
            SQLALCHEMY_DATABASE_URI = f"{LION_DEFAULT_SQLDB_PATH_BIND}"
        else:
            lion_config['SQLALCHEMY_BINDS'] = {'local_data_bind':  LION_DEFAULT_SQLDB_PATH_BIND}

        lion_config.update({
            'SQLALCHEMY_DATABASE_URI': str(SQLALCHEMY_DATABASE_URI),
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
