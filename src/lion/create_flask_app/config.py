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

        # SQLALCHEMY_DATABASE_URI = asyncio.run(azure_connection_with_retry())
        # if not SQLALCHEMY_DATABASE_URI:
        #     logging.warning("Azure SQL Database connection string not found or could not be established.")
        #     sys.exit(1)
            
        lion_config.setdefault('SQLALCHEMY_BINDS', {})

        # if not SQLALCHEMY_DATABASE_URI:
        #     # NOTE: Fallback to local DB if Azure connection string is not available
        #     # This is mainly for development and testing purposes. when trying to upload data to Azure,
        #     # we consolidate all data in the local DB called data.db first before pushing to Azure.
        #     SQLALCHEMY_DATABASE_URI = f"sqlite:///{paths.LION_DEFAULT_SQLDB_PATH / 'data.db'}"
        #     lion_config['SQLALCHEMY_BINDS'].update({'local_data_bind': SQLALCHEMY_DATABASE_URI})
        # else:
        
        lion_config['SQLALCHEMY_BINDS'].update({'local_data_bind':  LION_DEFAULT_SQLDB_PATH_BIND})

        lion_config.update({
            'SQLALCHEMY_DATABASE_URI': SQLALCHEMY_DATABASE_URI,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'LION_USER_ID': lion_config.get('LION_USER_ID', 'Guest')
            })

        user_group = getenv('LION_USER_GROUP_NAME', "UnknownGroup")
        lion_config.update({'LION_USER_ID': getenv('LION_USER_ID', 'Guest')})
        lion_config.update({'LION_OBJECT_ID': getenv('LION_OBJECT_ID', getenv('LION_USER_ID', 'Guest'))})
        lion_config.update({'LION_USER_GROUP_NAME': user_group})
        lion_config.update({'LION_USER_REGION_NAME': lion_config.get("LION_USER_REGION_NAME", "") if len(lion_config.get("LION_USER_REGION_NAME", "")) >= 2 else "GB"})
        lion_config.update({'LION_USER_LANGUAGE_NAME': lion_config.get("LION_USER_LANGUAGE_NAME", "") if len(lion_config.get("LION_USER_LANGUAGE_NAME", "")) >= 2 else "GB"})

        lion_config["SESSION_PERMANENT"] = True
        lion_config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

    except Exception as e:
        logging.error(f"[FATAL] Failed to load or parse flask config: {e}")
        return {}
    
    return lion_config

LION_CONFIG = configure_lion_app()
