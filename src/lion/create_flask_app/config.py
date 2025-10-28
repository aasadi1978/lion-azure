from datetime import timedelta
import logging
from os import getenv

from lion.bootstrap import LION_BOOTSTRAP_CONFIG as lion_config # Loaded first to setup env variables and logging in bootstrap\__init__.py
from lion.config import paths
from lion.create_flask_app.azure_sql_manager import SQLALCHEMY_DATABASE_URI

LION_DEFAULT_SQLDB_PATH_BIND = f"sqlite:///{paths.LION_DEFAULT_SQLDB_PATH / 'data.db'}"

def configure_lion_app() -> dict:
    """
    Setup the application configuration.
    """

    try:

        lion_config.setdefault('SQLALCHEMY_BINDS', {})
        lion_config['SQLALCHEMY_BINDS'].update({'local_data_bind':  LION_DEFAULT_SQLDB_PATH_BIND})

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
